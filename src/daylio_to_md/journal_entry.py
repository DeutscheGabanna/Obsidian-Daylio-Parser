"""
journal_entry.py focuses on processing and outputting individual entries, made at a particular moment. It is the most
atomic level of the journaling process.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:

└── all files
 └── a file from specific day
  └── **AN ENTRY FROM THAT DAY**
"""
from __future__ import annotations

import io
import logging
import typing
import datetime
from dataclasses import dataclass

from daylio_to_md.config import DEFAULTS
from daylio_to_md import utils, errors
from daylio_to_md.entry.mood import Moodverse


"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class NoMoodError(utils.ExpectedValueError):
    """Required non-empty mood."""
    def __init__(self, expected_value, actual_value):
        super().__init__(expected_value, actual_value)


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_MOOD = "Mood {} is missing from a list of known moods. Not critical, but colouring won't work on the entry."
    WRONG_TIME = "Received {}, expected valid time. Cannot create this entry without a valid time."
    WRONG_ACTIVITIES = "Received a non-empty string containing activities. Parsing it resulted in an empty list."


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


@dataclass(frozen=True)
class EntryBuilder:
    """
    Configure one instance of this, and you won't have to provide the same configuration
    over and over again when it instantiates new :class:`Entry` objects for you.
    :param csv_delimiter: Delimiter used to separate activities in Daylio .csv, e.g: football | chess
    :param header_multiplier: Headings level for each entry
    :param tag_activities: If set, tries to convert activities into valid frontmatter tags
    :param prefix: Add a given string before the header
    :param suffix: Add a given string after the header
    """
    csv_delimiter: str = DEFAULTS.csv_delimiter
    header_multiplier: int = DEFAULTS.header_level
    tag_activities: bool = DEFAULTS.tag_activities
    prefix: str = DEFAULTS.prefix
    suffix: str = DEFAULTS.suffix

    def build(self,
              time: typing.Union[datetime.time, str, typing.List[str], typing.List[int]],
              mood: str,
              activities: str = None,
              title: str = None,
              note: str = None,
              mood_set: Moodverse = Moodverse()) -> Entry:

        return Entry(
            utils.guess_time_type(time),
            mood,
            activities,
            title,
            note,
            self.csv_delimiter,
            self.header_multiplier,
            self.tag_activities,
            self.prefix,
            self.suffix,
            mood_set
        )


class Entry(utils.Core):
    """
    Journal entry

    :param time: Time at which this note was created. It will be type-casted into :class:`datetime.time` object.
    :param mood: Mood felt during writing this note.
                 It can be any :class:`str`, but during output the colouring won't work if the mood is not recognised.
                 (i.e `joyful` won't appear green if it isn't in the ``moods.json``)
    :param activities: Activities carried out around or at the time of writing the note
    :param title: Title of the note
    :param note: The contents of the journal note itself
    :param csv_delimiter: Delimiter used to separate activities in Daylio .csv, e.g: football | chess
    :param header_multiplier: Headings level for each entry
    :param tag_activities: If set, tries to convert activities into valid frontmatter tags
    :param prefix: Add a given string before the header
    :param suffix: Add a given string after the header
    :param mood_set: (opt.) Set if you want to use custom :class:`Moodverse` for mood handling
    :raise InvalidTimeError: if the passed time argument cannot be coerced into :class:`datetime.time`
    :raise NoMoorError: if mood is falsy
    """

    def __init__(self,
                 time: typing.Union[datetime.time, str, typing.List[str], typing.List[int]],
                 mood: str,
                 activities: str = None,
                 title: str = None,
                 note: str = None,
                 csv_delimiter: str = EntryBuilder.csv_delimiter,
                 header_multiplier: int = EntryBuilder.header_multiplier,
                 tag_activities: bool = EntryBuilder.tag_activities,
                 prefix: str = EntryBuilder.prefix,
                 suffix: str = EntryBuilder.suffix,
                 mood_set: Moodverse = Moodverse()):

        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__csv_delimiter = csv_delimiter
        self.__header_multiplier = header_multiplier
        self.__tag_activities = tag_activities
        self.__prefix = prefix
        self.__suffix = suffix

        # Processing required properties
        # ---
        # TIME
        # ---
        super().__init__(utils.guess_time_type(time))

        # ---
        # MOOD
        # ---
        if not mood:
            raise NoMoodError("any truthy string as mood", mood)

        # Check if the mood is valid - i.e. it does exist in the currently used Moodverse
        if mood not in mood_set.get_moods:
            self.__logger.warning(ErrorMsg.INVALID_MOOD.format(mood))
        # Warning is enough, it just disables colouring so not big of a deal
        self.__mood = mood

        # Processing other, optional properties
        # ---
        # Process activities
        self.__activities = []
        if activities:
            working_array = utils.strip_and_get_truthy(activities, self.__csv_delimiter)
            if len(working_array) > 0:
                for activity in working_array:
                    self.__activities.append(utils.slugify(activity, self.__tag_activities))
            else:
                self.__logger.warning(ErrorMsg.WRONG_ACTIVITIES.format(activities))
        # Process title
        self.__title = utils.slice_quotes(title) if title else None
        # Process note
        self.__note = utils.slice_quotes(note) if note else None

    def output(self, stream: io.IOBase | typing.IO) -> int:
        """
        Write entry contents directly into the provided buffer stream.
        It is the responsibility of the caller to handle the stream afterward.
        :param stream: Since it expects the base :class:`io.IOBase` class, it accepts both file and file-like streams.
        :raises utils.StreamError: if the passed stream does not support writing to it.
        :raises OSError: likely due to lack of space in memory or filesystem, depending on the stream
        :returns: how many characters were successfully written into the stream.
        """
        if not stream.writable():
            raise utils.StreamError

        chars_written = 0
        # HEADER OF THE NOTE
        # e.g. "## great | 11:00 AM | Oh my, what a night!"
        # header_multiplier is an int that multiplies the # to create headers in markdown
        header_elements = [
            self.__prefix,
            self.__mood,
            self.time.strftime("%H:%M"),
            self.__title,
            self.__suffix
        ]
        header = self.__header_multiplier * "#" + ' ' + ' | '.join([el for el in header_elements if el])
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
    def mood(self) -> str:
        return self.__mood

    @property
    def activities(self) -> typing.List[str]:
        return self.__activities

    @property
    def title(self) -> str:
        return self.__title

    @property
    def note(self) -> str:
        return self.__note

    @property
    def time(self) -> datetime.time:
        return self.uid

    def __str__(self):
        """:return: the time at which an entry was written in ``HH:MM`` format"""
        return self.uid.strftime("%H:%M")
