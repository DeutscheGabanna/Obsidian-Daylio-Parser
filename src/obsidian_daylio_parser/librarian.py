"""
Librarian is a Director/Orchestrator. It reads rows from a :class:`JournalReader` and assembles them
into a :class:`Journal` via :class:`EntriesFromBuilder`.

The parsing and I/O details are fully delegated:
    - **Input** is handled by a :class:`JournalReader` (CSV, SQLite, …)
    - **Output** is handled by a writer (e.g. :class:`MarkdownWriter`)
    - **Mood loading** is handled by :class:`Moodverse.from_file`

Librarian only owns the row-by-row domain assembly logic.

Usage::

    reader  = CsvJournalReader("backup.csv")
    mood_set = Moodverse.from_file("moods.json")
    journal = Librarian(reader, mood_set).parse()
    MarkdownWriter("/output").write_all(journal)
"""
from __future__ import annotations

import datetime
import logging
from os import PathLike

from obsidian_daylio_parser import utils, group, logs
from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.group import EntriesFrom, EntriesFromBuilder
from obsidian_daylio_parser.journal import Journal
from obsidian_daylio_parser.logs import logger
from obsidian_daylio_parser.reader import JournalReader, InvalidDataInFileError

"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class ErrorMsg(logs.LogMsg):
    STANDARD_MOODS_USED = "Standard mood set (rad, good, neutral, bad, awful) will be used."
    COUNT_ROWS = "{} rows of data found. Of that, {} were processed correctly."
    ROW_MISSING_VALUES = "Row {row}: not enough cells — expected {expected}, got {got}."
    ROW_INCOMPLETE = "Row {row}: required field missing or empty — {detail}."
    ROW_INVALID_DATE = "Row {row}: {detail}"
    ROW_UNEXPECTED_VALUE = "Row {row}: unexpected value, skipping."


class MissingValuesInRowError(utils.ExpectedValueError):
    """The row does not have enough cells - {} needed, {} available."""

    def __init__(self, cells_expected, cells_got):
        super().__init__(cells_expected, cells_got)


class CannotAccessJournalError(utils.CouldNotLoadFileError):
    """The journal {} could not be accessed or parsed."""

    def __init__(self, path: PathLike):
        super().__init__(path)


class EmptyJournalError(utils.CouldNotLoadFileError):
    """The journal {} did not produce any valid journal entries."""

    def __init__(self, path: PathLike):
        super().__init__(path)


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


class Librarian:
    """
    Orchestrates journal parsing by reading rows from a :class:`JournalReader`
    and assembling them into :class:`EntriesFrom` groups.

    Call :meth:`parse` to run the pipeline and receive a :class:`Journal`.

    :param reader: Any :class:`JournalReader` implementation (CSV, SQLite, …).
    :param mood_set: The :class:`Moodverse` to use for mood validation and colouring.
    :param entries_from_builder: Builder configured for creating :class:`EntriesFrom` groups.
    """

    EXPECTED_NUM_OF_CELLS = 8

    def __init__(self,
                 reader: JournalReader,
                 mood_set: Moodverse = None,
                 entries_from_builder: EntriesFromBuilder = EntriesFromBuilder()):

        self.__reader = reader
        self.__mood_set = mood_set or Moodverse()
        self.__entries_from_builder = entries_from_builder

    def parse(self) -> Journal:
        """
        Run the reader, assemble :class:`EntriesFrom` groups, and return a :class:`Journal`.

        :raises CannotAccessJournalError: if the source cannot be opened or is structurally invalid.
        :raises EmptyJournalError: if no valid entries were produced after processing all rows.
        :returns: a :class:`Journal` containing all successfully parsed entries.
        """
        if not self.__mood_set.get_custom_moods:
            logger.info(ErrorMsg.STANDARD_MOODS_USED)

        known_dates: dict[datetime.date, EntriesFrom] = {}
        lines_total = 0
        lines_ok = 0

        try:
            for csv_row, line in enumerate(self.__reader.read(), start=2):
                lines_total += 1
                try:
                    if self.__process_line(line, known_dates, csv_row):
                        lines_ok += 1
                except MissingValuesInRowError as err:
                    logger.warning(ErrorMsg.ROW_MISSING_VALUES.format(
                        row=csv_row, expected=err.expected_value, got=err.actual_value
                    ))
        except (utils.CouldNotLoadFileError, InvalidDataInFileError) as err:
            raise CannotAccessJournalError(self.__reader.source) from err

        logger.info(ErrorMsg.COUNT_ROWS.format(lines_total, lines_ok))

        if lines_ok == 0:
            raise EmptyJournalError(self.__reader.source)

        return Journal(known_dates, self.__mood_set)

    def __process_line(self, line: dict[str, str],
                       known_dates: dict[datetime.date, EntriesFrom],
                       csv_row: int) -> bool:
        """
        Process a single row and add it to the appropriate :class:`EntriesFrom` group.

        :param line: a dictionary with values from the currently processed row.
        :param known_dates: mutable dict accumulating date -> EntriesFrom mappings.
        :param csv_row: 1-based line number of this row in the source file (header = 1, first data row = 2).
        :return: True if the row was processed successfully, False otherwise.
        :raises MissingValuesInRowError: if the row lacks enough cells.
        """
        if len(line) < self.EXPECTED_NUM_OF_CELLS:
            raise MissingValuesInRowError(self.EXPECTED_NUM_OF_CELLS, len(line))

        try:
            date = utils.guess_date_type(line["full_date"])
            entries_from_this_date = known_dates.get(date)
            if entries_from_this_date is None:
                entries_from_this_date = self.__entries_from_builder.build(date, self.__mood_set)
            entries_from_this_date.create_entry(line)
            known_dates[date] = entries_from_this_date
        except group.TriedCreatingDuplicateDatedEntryError:
            return False
        except group.IncompleteDataRow as err:
            logger.warning(ErrorMsg.ROW_INCOMPLETE.format(row=csv_row, detail=str(err)))
            return False
        except (utils.InvalidDateError, utils.InvalidTimeError) as err:
            logger.warning(ErrorMsg.ROW_INVALID_DATE.format(row=csv_row, detail=err.__doc__))
            return False
        except ValueError:
            logger.warning(ErrorMsg.ROW_UNEXPECTED_VALUE.format(row=csv_row))
            return False
        return True
