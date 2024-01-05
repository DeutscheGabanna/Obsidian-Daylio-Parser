"""
dated_entry focuses on building the individual entries, made at a particular moment, as objects.
It is the most atomic level of the journaling process.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> notes written on a particular date -> _A PARTICULAR NOTE_
"""
import logging
import re
from typing import Match
from typing import List

from config import options
import errors
import utils

# Adding DatedEntry-specific options in global_settings
dated_entry_settings = options.get_console().add_argument_group(
    "Dated Entries",
    "Handles how entries should be formatted"
)
dated_entry_settings.add_argument(
    "--tags",
    help="Tags in the YAML of each note.",
    nargs='*',  # this allows, for example, "--tags one two three" --> ["one", "two", "three"]
    default="daily",
    dest="TAGS"
)
dated_entry_settings.add_argument(
    "--prefix",  # <here's your prefix>YYYY-MM-DD.md so remember about a separating char
    default='',
    help="Prepends a given string to each entry's header."
)
dated_entry_settings.add_argument(
    "--suffix",  # YYYY-MM-DD<here's your suffix>.md so remember about a separating char
    default='',
    help="Appends a given string at the end of each entry's header."
)
dated_entry_settings.add_argument(
    "--tag_activities", "-a",
    action="store_true",  # default=True
    help="Tries to convert activities into valid tags.",
    dest="ACTIVITIES_AS_TAGS"
)
dated_entry_settings.add_argument(
    "-colour", "--color",
    action="store_true",  # default=True
    help="Prepends a colour emoji to each entry depending on mood.",
    dest="colour"
)
dated_entry_settings.add_argument(
    "--header",
    type=int,
    default=2,
    help="Headings level for each entry.",
    dest="HEADER_LEVEL"
)
dated_entry_settings.add_argument(
    "--csv-delimiter",
    default="|",
    help="Set delimiter for activities in Daylio .CSV, e.g: football | chess"
)


class IsNotTimeError(utils.CustomException):
    """Expected a string in a valid time format - HH:MM with optional AM/PM suffix."""


def is_time_format_valid(string: str) -> Match[str] | None:
    """
    Is the time format of :param:`str` valid?
    :param string: time to check
    :return: ``True`` if :param:`str` follows the ``HH:MM`` format, with optional AM/PM appended, ``False`` otherwise
    """
    return re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]($|\sAM|\sPM)').match(string)


def is_time_range_valid(string: str) -> bool:
    """
    Is the time range of :param:`str` valid?
    :param string: time to check
    :return: ``True`` if hour and minute ranges are both ok, ``False`` otherwise
    """
    time_array = string.strip().split(':')

    # Check if it's in 12-hour format (AM/PM) or 24-hour format
    if 'AM' in string or 'PM' in string:
        is_hour_ok = 0 <= int(time_array[0]) <= 12
    else:
        is_hour_ok = 0 <= int(time_array[0]) < 24

    # Minutes can be checked irrespective of AM/PM/_ notation
    is_minutes_ok = 0 <= int(time_array[1][:2]) < 60

    return all((is_hour_ok, is_minutes_ok))


def slice_quotes(string: str) -> str:
    """
    Gets rid of initial and terminating quotation marks inserted by Daylio
    :param string: string to be sliced
    :returns: string without quotation marks in the beginning and end of the initial string, even if it means empty str.
    """
    if string is not None and len(string) > 2:
        return string.strip("\"")
    # only 2 characters? Then it is an empty cell.
    return ""


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_MOOD = "Mood {} is missing from a list of known moods. Colouring won't work for this one."
    WRONG_PARENT = "Object of class {} is trying to instantiate {} as child. This will end badly."


class Time:
    """
    Hour and minutes of a particular moment in time. Validates the time string on instantiation.
    str(instance) returns the valid time in the ``HH:MM`` format.
    :raises IsNotTimeError: if string is not a valid time in ``HH:MM`` format (either AM/PM or 24h)
    """

    def __init__(self, string: str):
        """
        Upon instantiation checks if the time is valid.
        Used in :class:`DatedEntry` to create an instance of this class.
        :raises IsNotTime: if string is not a valid time in ``HH:MM`` format with optional AM/PM appended
        :param string: time in ``HH:MM`` format - can have AM/PM appended
        """
        self.__logger = logging.getLogger(self.__class__.__name__)

        # OK
        if is_time_format_valid(string) and is_time_range_valid(string):
            time_array = string.strip().split(':')
            self.__hour = time_array[0]
            self.__minutes = time_array[1]

        # NOT OK
        else:
            msg_on_error = ErrorMsg.print(ErrorMsg.WRONG_VALUE, string, "HH:MM (AM/PM/)")
            self.__logger.warning(msg_on_error)
            raise IsNotTimeError(msg_on_error)

    def __str__(self) -> str:
        """
        :return: Outputs its hour and minutes attributes as a string in valid time format - HH:MM.
        """
        return ':'.join([self.__hour, self.__minutes])


class DatedEntry(utils.Core):
    """
    Journal entry.
    **A journal entry cannot exists without:**

    * Time it was written at, as :class:`Time`
    * Mood, that is -  a dominant emotional state during that particular moment in time.

    **Other, optional attributes:**

    * title
    * note
    * activities performed during or around this time

    :raises ValueError: if at least one of the required attributes cannot be set properly
    """

    def __init__(self,
                 time: str,
                 mood: str,
                 known_moods: dict[str, List[str]],
                 activities: str = None,
                 title: str = None,
                 note: str = None):
        # TODO: have to test the whole instantiation function again after refactoring
        self.__logger = logging.getLogger(self.__class__.__name__)

        # Processing required properties
        # ---
        # Time
        try:
            super().__init__(Time(time))
        except IsNotTimeError:
            raise ValueError("Cannot create object without valid Time attribute")

        # Mood
        if len(mood) == 0 or mood is None:
            raise ValueError("Cannot create object without valid Mood attribute")
        else:
            mood_is_in_dictionary = False
            for i, (_, this_group) in enumerate(known_moods.items()):
                if mood in this_group:
                    mood_is_in_dictionary = True
                    break
            if not mood_is_in_dictionary:
                self.__logger.warning(ErrorMsg.print(ErrorMsg.INVALID_MOOD, mood))
            # Assign it anyway. Warning is enough.
            self.__mood = mood

        # Processing other, optional properties
        # ---
        # Process activities
        self.__activities = []
        array = slice_quotes(activities).split(options.csv_delimiter)
        if len(array) > 0:
            for activity in array:
                self.__activities.append(utils.slugify(
                    activity,
                    options.tag_activities
                ))

        # Process title
        self.__title = None
        if title is not None and len(title) > 0:
            self.__title = slice_quotes(title)

        # Process note
        self.__note = None
        if note is not None and len(note) > 0:
            self.__note = slice_quotes(note)

    @property
    def mood(self):
        return self.__mood

    @property
    def activities(self):
        return self.__activities

    @property
    def title(self):
        return self.__title

    @property
    def note(self):
        return self.__note
