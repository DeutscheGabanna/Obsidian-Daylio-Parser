"""
This file specialises in building the middleware between actual journal entries and the whole journal.
It creates and organises only those entries written on a particular date. This way they can be handled easier.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> _NOTES WRITTEN ON A PARTICULAR DATE_ -> a particular note
"""
import re
import logging

import dated_entry
import errors
from typing import List
from dated_entry import DatedEntry
import utils
from config import options


class DatedEntryMissingError(utils.CustomException):
    pass


class IncompleteDataRow(utils.CustomException):
    pass


class InvalidDateError(utils.CustomException):
    pass


class TriedCreatingDuplicateDatedEntryError(utils.CustomException):
    pass


class ErrorMsg(errors.ErrorMsgBase):
    CSV_ROW_INCOMPLETE_DATA = "Passed .csv contains rows with invalid data. Tried to parse {} as date."


class Date:
    """
    Day, month and year of a particular date. Validates the date string on instantiation.
    """

    def __init__(self, string: str):
        """
        :raises InvalidDateError: if :param:`string` is not a valid date (for example the month number > 12)
        :param string: on which entries have been created (`YYYY-MM-DD`)
        """
        self.__logger = logging.getLogger(self.__class__.__name__)

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


class DatedEntriesGroup(utils.Core):
    """
    A particular date which groups entries written that day.

    Imagine it as a scribe, holding a stack of papers in his hand.
    The master Librarian knows each one of the scribes, including this one.
    However, the scribe knows only his papers. The papers contain all entries written that particular date.
    """

    def __init__(self, date):
        self.__logger = logging.getLogger(self.__class__.__name__)
        super().__init__()

        try:
            self.set_uid(Date(date))
        except InvalidDateError:
            self.__logger.warning(ErrorMsg.print(ErrorMsg.WRONG_VALUE, date, "YYYY-MM-DD"))
            raise ValueError
        else:
            self.__hash = hash(self.get_uid())
            self.__known_dated_entries = {}

    def __hash__(self):
        return self.__hash

    def __bool__(self):
        """
        :return: ``True`` if itself has any :class:`DatedEntry` children
        """
        return all((
            super().__bool__(),
            len(self.__known_dated_entries) > 0
        ))

    def create_dated_entry_from_row(self,
                                    line: dict[str],
                                    known_moods: dict[List[str]] = None) -> dated_entry.DatedEntry:
        """
        :func:`access_dated_entry` of :class:`DatedEntry` object with the specified parameters.
        :raises TriedCreatingDuplicateDatedEntryError: if it would result in making a duplicate :class:`DatedEntry`
        :raises IncompleteDataRow: if ``line`` does not have ``time`` and ``mood`` keys at the very least
        :param line: a dictionary of strings. Required keys: mood, activities, note_title & note.
        :param known_moods: each key of the dict should have a set of strings containing moods.
        """
        # TODO: test case this
        # Try accessing the minimum required keys
        for key in ["time", "mood"]:
            try:
                line[key]
            except KeyError:
                raise IncompleteDataRow(key)

        # Check if there's already an object with this time
        if line["time"] in self.__known_dated_entries:
            raise TriedCreatingDuplicateDatedEntryError
        else:
            # Instantiate the entry
            entry = dated_entry.DatedEntry(
                line["time"],
                line["mood"],
                self,
                known_moods,
                activities=line["activities"],
                title=line["title"],
                note=line["note"]
            )
        return entry

    def access_dated_entry(self, time: str) -> DatedEntry:
        """
        Retrieve an already existing DatedEntry object.
        :param time: any string, but if it's not a valid HH:MM format then I guarantee it won't be found either way
        :raises DatedEntryMissingError: if the entry specified in ``time`` does not exist
        :returns: :class:`DatedEntry`
        """
        try:
            ref = self.__known_dated_entries[time]
        except KeyError:
            msg = ErrorMsg.print(ErrorMsg.OBJECT_NOT_FOUND, time)
            self.__logger.warning(msg)
            raise DatedEntryMissingError(msg)
        else:
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_FOUND, time))
            return ref
