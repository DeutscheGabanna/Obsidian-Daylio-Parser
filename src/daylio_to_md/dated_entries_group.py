"""
This file specialises in building the middleware between actual journal entries and the whole journal.
It creates and organises only those entries written on a particular date. This way they can be handled easier.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> _NOTES WRITTEN ON A PARTICULAR DATE_ -> a particular note
"""
from __future__ import annotations

import io
import logging
import re

import typing

from daylio_to_md import dated_entry
from daylio_to_md import utils, errors
from daylio_to_md.dated_entry import DatedEntry
from daylio_to_md.entry.mood import Moodverse
from daylio_to_md.config import options


class DatedEntryMissingError(utils.CustomException):
    """The :class:`DatedEntry` does not exist."""


class IncompleteDataRow(utils.CustomException):
    """Passed a row of data from CSV file that does not have all required fields."""


class InvalidDateError(utils.CustomException):
    """String is not a valid date. Check :class:`Date` for details."""


class TriedCreatingDuplicateDatedEntryError(utils.CustomException):
    """Tried to create object of :class:`DatedEntry` that would be a duplicate of one that already exists."""


class ErrorMsg(errors.ErrorMsgBase):
    CSV_ROW_INCOMPLETE_DATA = "Passed .csv contains rows with invalid data. Tried to parse {} as date."


class Date:
    """
    Day, month and year of a particular date. Validates the date string on instantiation.
    """
    _instances = {}  # Class variable to store instances based on date

    def __new__(cls, string: str):
        # Check if an instance for the given date already exists
        if string in cls._instances:
            return cls._instances[string]
        # If not, create a new instance
        instance = super(Date, cls).__new__(cls)
        cls._instances[string] = instance
        return instance

    def __init__(self, string: str):
        """
        :raises InvalidDateError: if :param:`string` is not a valid date (for example the month number > 12)
        :param string: on which entries have been created (`YYYY-MM-DD`)
        """
        # self.__logger = logging.getLogger(self.__class__.__name__)

        # does it have a valid format YYYY-MM-DD
        valid_date_pattern = re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$')
        if not re.match(valid_date_pattern, string):
            raise InvalidDateError

        # does it have valid ranges? (year ranges are debatable)
        date_array = string.strip().split('-')
        if not all((
                1900 < int(date_array[0]) < 2100,
                0 < int(date_array[1]) < 13,
                0 < int(date_array[2][:2]) < 32)):
            raise InvalidDateError

        self.__year = date_array[0]
        self.__month = date_array[1]
        self.__day = date_array[2]

    def __str__(self) -> str:
        """
        :return: returns the valid date in the YYYY-MM-DD format. This is the superior format, end of discussion.
        """
        return '-'.join([self.__year, self.__month, self.__day])

    def __eq__(self, other: 'Date') -> bool:
        """Used only for comparing two :class:`Date` objects - itself and another one."""
        if isinstance(other, Date):
            return all((other.year == self.year,
                        other.month == self.month,
                        other.day == self.day))
        return super().__eq__(other)

    @property
    def year(self):
        return self.__year

    @property
    def month(self):
        return self.__month

    @property
    def day(self):
        return self.__day


class DatedEntriesGroup(utils.Core):
    """
    A particular date which groups entries written that day.

    Imagine it as a scribe, holding a stack of papers in his hand.
    The master Librarian knows each one of the scribes, including this one.
    However, the scribe knows only his papers. The papers contain all entries written that particular date.

    Truthy if it knows at least one :class:`DatedEntry` made on this :class:`Date`.
    """
    _instances = {}

    def __new__(cls, date: str, current_mood_set: Moodverse = Moodverse()):
        # Check if an instance for the given date already exists
        if date in cls._instances:
            return cls._instances[date]
        # If not, create a new instance
        instance = super(DatedEntriesGroup, cls).__new__(cls)
        cls._instances[date] = instance
        return instance

    def __init__(self, date, current_mood_set: Moodverse = Moodverse()):
        """
        :raises InvalidDateError: if the date string is deemed invalid by :class:`Date`
        :param date: The date for all child entries within.
        :param current_mood_set: Use custom :class:`Moodverse` or default if not provided.
        """
        self.__logger = logging.getLogger(self.__class__.__name__)

        # Try parsing the date and assigning it as your identification (uid)
        try:
            super().__init__(Date(date))
        # Date is no good?
        except InvalidDateError as err:
            msg = ErrorMsg.print(ErrorMsg.WRONG_VALUE, date, "YYYY-MM-DD")
            self.__logger.warning(msg)
            raise InvalidDateError(msg) from err

        # All good - initialise
        self.__known_entries_for_this_date: dict[str, DatedEntry] = {}
        self.__known_moods: Moodverse = current_mood_set

    def append_to_known(self, entry: DatedEntry) -> None:
        self.__known_entries_for_this_date[str(entry.uid)] = entry

    def create_dated_entry_from_row(self,
                                    line: dict[str, str]) -> dated_entry.DatedEntry:
        """
        :func:`access_dated_entry` of :class:`DatedEntry` object with the specified parameters.
        :raises TriedCreatingDuplicateDatedEntryError: if it would result in making a duplicate :class:`DatedEntry`
        :raises IncompleteDataRow: if ``line`` does not have ``time mood`` keys at the very least, or either is empty
        :raises ValueError: re-raises ValueError from :class:`DatedEntry`
        :param line: a dictionary of strings. Required keys: mood, activities, note_title & note.
        """
        # TODO: test case this
        # Try accessing the minimum required keys
        for key in ["time", "mood"]:
            try:
                line[key]
            except KeyError as err:
                raise IncompleteDataRow(key) from err
            # is it empty then, maybe?
            if not line[key]:
                raise IncompleteDataRow(key)

        # Check if there's already an object with this time
        # TODO: Daylio actually allows creating multiple entries and mark them as written at the same time
        if line["time"] in self.__known_entries_for_this_date:
            raise TriedCreatingDuplicateDatedEntryError

        # Instantiate the entry
        try:
            this_entry = dated_entry.DatedEntry(
                line["time"],
                line["mood"],
                activities=line["activities"],
                title=line["note_title"],
                note=line["note"],
                override_mood_set=self.__known_moods
            )
        except ValueError as err:
            raise ValueError from err

        self.append_to_known(this_entry)
        return this_entry

    def access_dated_entry(self, time: str) -> DatedEntry:
        """
        Retrieve an already existing DatedEntry object.
        :param time: any string, but if it's not a valid HH:MM format then I guarantee it won't be found either way
        :raises DatedEntryMissingError: if the entry specified in ``time`` does not exist
        :returns: :class:`DatedEntry`
        """
        try:
            ref = self.__known_entries_for_this_date[time]
        except KeyError as err:
            msg = ErrorMsg.print(ErrorMsg.OBJECT_NOT_FOUND, time)
            self.__logger.warning(msg)
            raise DatedEntryMissingError(msg) from err
        self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_FOUND, time))
        return ref

    def output(self, stream: io.IOBase | typing.IO) -> int:
        """
        Write entry contents of all :class:`DatedEntry` known directly into the provided buffer stream.
        It is the responsibility of the caller to handle the stream afterward.
        :raises utils.StreamError: if the passed stream does not support writing to it.
        :raises OSError: likely due to lack of space in memory or filesystem, depending on the stream
        :param stream: Since it expects the base :class:`io.IOBase` class, it accepts both file and file-like streams.
        :returns: how many characters were successfully written into the stream.
        """
        if not stream.writable():
            raise utils.StreamError

        chars_written = 0
        # THE BEGINNING OF THE FILE
        # when appending file tags at the beginning of the file, discard any duplicates or falsy strings
        # sorted() is used to have a deterministic order, set() was random, so I couldn't properly test the output
        valid_tags = sorted(set(val for val in options.tags if val))
        if valid_tags:
            # why '\n' instead of os.linesep?
            # > Do not use os.linesep as a line terminator when writing files opened in text mode (the default);
            # > use a single '\n' instead, on all platforms.
            # https://docs.python.org/3.10/library/os.html#os.linesep
            chars_written += stream.write("---" + "\n")
            chars_written += stream.write("tags: " + ",".join(valid_tags) + "\n")
            chars_written += stream.write("---" + "\n"*2)

        # THE ACTUAL ENTRY CONTENTS
        # Each DatedEntry object now appends its contents into the stream
        for entry in self.__known_entries_for_this_date.values():
            # write returns the number of characters successfully written
            # https://docs.python.org/3/library/io.html#io.TextIOBase.write
            if entry.output(stream) > 0:
                chars_written += stream.write("\n"*2)

        return chars_written

    @property
    def known_entries_from_this_day(self):
        return self.__known_entries_for_this_date

    @property
    def date(self):
        """
        :return: String in the format of YYYY-MM-DD that identifies this specific object of :class:`DatedEntryGroup`.
        """
        return self.uid
