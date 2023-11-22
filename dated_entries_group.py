"""
This file specialises in building the middleware between actual journal entries and the whole journal.
It creates and organises only those entries written on a particular date. This way they can be handled easier.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> _NOTES WRITTEN ON A PARTICULAR DATE_ -> a particular note
"""
import re
import logging
import errors
from dated_entry import DatedEntry
import utils


class ErrorMsg(errors.ErrorMsgBase):
    CSV_ROW_INCOMPLETE_DATA = "Passed .csv contains rows with invalid data. Tried to parse {} as date."


class Date:
    """
    Day, month and year of a particular date. Validates the date string on instantiation.
    str(instance) returns the valid date in the YYYY-MM-DD format.
    """
    def __init__(self, string):
        self.__logger = logging.getLogger(self.__class__.__name__)

        # does it have a valid format YYYY-MM-DD
        valid_date_pattern = re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$')
        msg_on_error = ErrorMsg.print(ErrorMsg.WRONG_VALUE, string, "YYYY-MM-DD")
        if not re.match(valid_date_pattern, string):
            self.__logger.warning(msg_on_error)
            raise ValueError

        # does it have valid ranges? (year ranges are debatable)
        date_array = string.strip().split('-')
        if not all((
                1900 < int(date_array[0]) < 2100,
                0 < int(date_array[1]) < 13,
                0 < int(date_array[2][:2]) < 32)):
            self.__logger.warning(msg_on_error)
            raise ValueError

        self.__year = date_array[0]
        self.__month = date_array[1]
        self.__day = date_array[2]

    def __str__(self):
        return '-'.join([self.__year, self.__month, self.__day])


class DatedEntriesGroup(utils.Core):
    """
    A particular date which groups entries written that day.
    Raises ValueError if instantiated with a wrong date format.
    Otherwise, it is truthy if it has any DatedEntry children, or falsy if it does not.

    Imagine it as a scribe, holding a stack of papers in his hand.
    The master Librarian knows each one of the scribes, including this one.
    However, the scribe knows only his papers. The papers contain all entries written that particular date.
    """

    def __init__(self, date):
        self.__logger = logging.getLogger(self.__class__.__name__)
        super().__init__()
        self.set_uid(Date(date))

        self.__hash = hash(self.get_uid())
        self.__known_dated_entries = {}

    def __hash__(self):
        return self.__hash

    def __bool__(self):
        return all((
            super().__bool__(),
            len(self.__known_dated_entries) > 0
        ))

    def access_dated_entry(self, time):
        """
        Retrieve an already existing DatedEntry object or create if missing.
        Object is accessed or created only if the format is valid.
        If the time format is invalid, it returns ValueError on DatedEntry instantiation.
        """
        # do you already have an entry from that time?
        if time in self.get_known_dated_entries():
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_FOUND, time))
            return self.__known_dated_entries[time]
        else:
            dated_entry_obj = DatedEntry(time, parent=self)
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_NOT_FOUND, time))
            self.__known_dated_entries[time] = dated_entry_obj
            return dated_entry_obj

    def get_known_dated_entries(self):
        """
        Retrieve the list of known entries. Returns a dictionary of keys.
        If it is queried, the method does not validate the correctness of the query.
        """
        return self.__known_dated_entries
