"""
dated_entry focuses on building the individual entries, made at a particular moment, as objects.
It is the most atomic level of the journaling process.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> notes written on a particular date -> _A PARTICULAR NOTE_
"""
from __future__ import annotations

import logging
import re
import io
from typing import Match

import typing

from daylio_to_md import utils, errors
from daylio_to_md.config import options
from daylio_to_md.entry.mood import Moodverse

# Adding DatedEntry-specific options in global_settings
dated_entry_settings = options.arg_console.add_argument_group(
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
    msg = "Expected HH:MM (+ optionally AM/PM suffix) but got {} instead."

    def __init__(self, tried_time: str):
        super().__init__(type(self).msg.format(tried_time))


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


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_MOOD = "Mood {} is missing from a list of known moods. Not critical, but colouring won't work on the entry."
    WRONG_TIME = "Received {}, expected valid time. Cannot create this entry without a valid time."
    WRONG_ACTIVITIES = "Expected a non-empty list of activities. In that case just omit this argument in function call."
    WRONG_TITLE = "Expected a non-empty title. Omit this argument in function call rather than pass a falsy string."
    WRONG_NOTE = "Expected a non-empty note. Omit this argument in function call rather than pass a falsy string."


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
        if is_time_format_valid(string.strip()) and is_time_range_valid(string.strip()):
            time_array = string.strip().split(':')
            self.__hour = time_array[0]
            self.__minutes = time_array[1]

        # NOT OK
        else:
            self.__logger.warning(IsNotTimeError.msg.format(string))
            raise IsNotTimeError(string)

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
                 activities: str = None,
                 title: str = None,
                 note: str = None,
                 override_mood_set: Moodverse = Moodverse()):
        """
        :param time: Time at which this note was created
        :param mood: Mood felt during writing this note
        :param activities: (opt.) Activities carried out around or at the time of writing the note
        :param title: (opt.) Title of the note
        :param note: (opt.) The contents of the journal note itself
        :param override_mood_set: Set if you want to use custom :class:`Moodverse` for mood handling
        """
        # TODO: have to test the whole instantiation function again after refactoring
        self.__logger = logging.getLogger(self.__class__.__name__)

        # Processing required properties
        # ---
        # TIME
        # ---
        try:
            super().__init__(Time(time))
        except IsNotTimeError as err:
            errors.ErrorMsgBase.print(ErrorMsg.WRONG_TIME, time)
            raise ValueError from err

        # ---
        # MOOD
        # ---
        if not mood:
            raise ValueError
        # Check if the mood is valid - i.e. it does exist in the currently used Moodverse
        if not override_mood_set.get_mood(mood):
            errors.ErrorMsgBase.print(ErrorMsg.INVALID_MOOD, mood)
        # Warning is enough, it just disables colouring so not big of a deal
        self.__mood = mood

        # Processing other, optional properties
        # ---
        # Process activities
        # ---
        self.__activities = []
        if activities:
            working_array = utils.strip_and_get_truthy(activities, options.csv_delimiter)
            if len(working_array) > 0:
                for activity in working_array:
                    self.__activities.append(utils.slugify(
                        activity,
                        options.tag_activities
                    ))
            else:
                errors.ErrorMsgBase.print(ErrorMsg.WRONG_ACTIVITIES)
        # ---
        # Process title
        # ---
        self.__title = utils.slice_quotes(title) if title else None
        if not title:
            errors.ErrorMsgBase.print(ErrorMsg.WRONG_TITLE)
        # ---
        # Process note
        # ---
        self.__note = utils.slice_quotes(note) if note else None
        if not note:
            errors.ErrorMsgBase.print(ErrorMsg.WRONG_NOTE)

    def output(self, stream: io.IOBase | typing.IO) -> int:
        """
        Write entry contents directly into the provided buffer stream.
        It is the responsibility of the caller to handle the stream afterward.
        :raises utils.StreamError: if the passed stream does not support writing to it.
        :raises OSError: likely due to lack of space in memory or filesystem, depending on the stream
        :param stream: Since it expects the base :class:`io.IOBase` class, it accepts both file and file-like streams.
        :returns: how many characters were successfully written into the stream.
        """
        if not stream.writable():
            raise utils.StreamError

        chars_written = 0
        # HEADER OF THE NOTE
        # e.g. "## great | 11:00 AM | Oh my, what a night!"
        # options.header is an int that multiplies the # to create headers in markdown
        header_elements = [
            options.header * "#" + ' ' + self.__mood,
            self.time,
            self.__title
        ]
        header = ' | '.join([el for el in header_elements if el is not None])
        chars_written += stream.write(header)
        # ACTIVITIES
        # e.g. "bicycle skating pool swimming"
        if len(self.__activities) > 0:
            chars_written += stream.write("\n" + ' '.join(self.__activities))
        # NOTE
        # e.g. "Went swimming this evening."
        if self.__note is not None:
            chars_written += stream.write("\n" + self.__note)

        return chars_written

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

    @property
    def time(self):
        return str(self.uid)
