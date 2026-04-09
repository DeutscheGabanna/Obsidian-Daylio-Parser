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
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn

import logging
import datetime

from obsidian_daylio_parser import utils, errors, group
from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.group import EntriesFrom, EntriesFromBuilder
from obsidian_daylio_parser.journal import Journal
from obsidian_daylio_parser.reader import JournalReader, InvalidDataInFileError


"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class ErrorMsg(errors.ErrorMsgBase):
    STANDARD_MOODS_USED = "Standard mood set (rad, good, neutral, bad, awful) will be used."
    COUNT_ROWS = "{} rows of data found. Of that, {} were processed correctly."


class MissingValuesInRowError(utils.ExpectedValueError):
    """The row does not have enough cells - {} needed, {} available."""

    def __init__(self, cells_expected, cells_got):
        super().__init__(cells_expected, cells_got)


class CannotAccessJournalError(utils.CouldNotLoadFileError):
    """The journal {} could not be accessed or parsed."""

    def __init__(self, path: str):
        super().__init__(path)


class EmptyJournalError(utils.CouldNotLoadFileError):
    """The journal {} did not produce any valid journal entries."""

    def __init__(self, path: str):
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

        self.__logger = logging.getLogger(self.__class__.__name__)
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
            self.__logger.info(ErrorMsg.STANDARD_MOODS_USED)

        known_dates: dict[datetime.date, EntriesFrom] = {}
        lines_total = 0
        lines_ok = 0

        try:
            for line in self.__reader.read():
                lines_total += 1
                try:
                    if self.__process_line(line, known_dates):
                        lines_ok += 1
                except MissingValuesInRowError as err:
                    self.__logger.warning(err.__doc__)
        except (utils.CouldNotLoadFileError, InvalidDataInFileError) as err:
            raise CannotAccessJournalError(self.__reader.source) from err

        self.__logger.info(ErrorMsg.COUNT_ROWS.format(lines_total, lines_ok))

        if lines_ok == 0:
            raise EmptyJournalError(self.__reader.source)

        return Journal(known_dates, self.__mood_set)

    def __process_line(self, line: dict[str, str],
                       known_dates: dict[datetime.date, EntriesFrom]) -> bool:
        """
        Process a single row and add it to the appropriate :class:`EntriesFrom` group.

        :param line: a dictionary with values from the currently processed row.
        :param known_dates: mutable dict accumulating date -> EntriesFrom mappings.
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
        except (group.TriedCreatingDuplicateDatedEntryError,
                group.IncompleteDataRow,
                utils.InvalidDateError,
                ValueError):
            return False
        return True

