"""
Abstracts away the journal source format (CSV, SQLite, etc.) from the Librarian.
Each reader validates its source and yields rows as dicts that the Librarian can feed into EntriesFromBuilder.

To add support for a new format, subclass :class:`JournalReader` and implement :meth:`read` and :attr:`source`.
"""
from __future__ import annotations

import logging
import typing
from abc import ABC, abstractmethod
from os import PathLike

from obsidian_daylio_parser import utils, logs
from obsidian_daylio_parser.logs import logger

"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class ErrorMsg(logs.LogMsg):
    CSV_ALL_FIELDS_PRESENT = "All expected columns are present in the CSV file columns."
    CSV_FIELDS_MISSING = "The following expected columns are missing: {}"
    CSV_NEW_FIELDS_MISSING = "This seems to be an old Daylio export without the new fields: {}. They are optional."


class InvalidDataInFileError(utils.ExpectedValueError):
    """The file does not follow the expected structure."""

    def __init__(self, expected_value, actual_value):
        super().__init__(expected_value, actual_value)


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


class JournalReader(ABC):
    """
    Contract: open a journal source, validate its structure, and yield rows as dicts.
    Each yielded dict must have at minimum the keys: ``full_date``, ``time``, ``mood``.

    Implementers must provide:
        - :meth:`read` — a generator that yields one dict per journal entry
        - :attr:`source` — a human-readable description of the source (e.g. filepath, db path)
    """

    EXPECTED_FIELDS = (
        "full_date",
        "date",
        "weekday",
        "time",
        "mood",
        "activities",
        "note_title",
        "note",
    )

    # fields not present in older Daylio .csv, for backwards compatibility
    OPTIONAL_FIELDS = (
        "scales",
    )

    @classmethod
    def check_fields(cls, present: tuple[str, ...], expected: tuple[str, ...]):
        return [ field for field in expected if field not in present ]

    @property
    @abstractmethod
    def source(self) -> PathLike:
        """A human-readable description of the source (e.g. a filepath)."""
        ...

    @abstractmethod
    def read(self) -> typing.Iterator[dict[str, str]]:
        """
        Yield one ``dict[str, str]`` per journal entry row.

        :raises utils.CouldNotLoadFileError: if the source cannot be opened.
        :raises InvalidDataInFileError: if the source structure is invalid.
        """
        ...


class CsvJournalReader(JournalReader):
    """
    Reads and validates a Daylio CSV export.
    Opens the file, checks that all expected columns are present, and yields one dict per row.
    """

    def __init__(self, filepath: PathLike):
        self.__filepath = filepath

    @property
    def source(self) -> PathLike:
        return self.__filepath

    def read(self) -> typing.Iterator[dict[str, str]]:
        """
        :raises utils.CouldNotLoadFileError: if the CSV cannot be opened or decoded.
        :raises InvalidDataInFileError: if required columns are missing from the CSV header.
        """

        try:
            with utils.CsvLoader().load(self.__filepath) as file:
                # Validate that all expected columns are present
                missing = self.check_fields(file.fieldnames, self.EXPECTED_FIELDS)
                if missing:
                    msg = ErrorMsg.CSV_FIELDS_MISSING.format(', '.join(missing))
                    logger.critical(msg)
                    raise InvalidDataInFileError(file.fieldnames, msg)

                logger.debug(ErrorMsg.CSV_ALL_FIELDS_PRESENT)
                optionals = self.check_fields(file.fieldnames, self.OPTIONAL_FIELDS)
                if optionals:
                    msg = ErrorMsg.CSV_NEW_FIELDS_MISSING.format(', '.join(optionals))
                    logger.info(msg)

                for line in file:
                    yield line

        except (utils.CouldNotLoadFileError, InvalidDataInFileError):
            # Re-raise these directly — they are expected error types
            raise
        except ValueError as err:
            raise utils.CouldNotLoadFileError(self.__filepath) from err
