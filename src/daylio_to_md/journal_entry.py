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

from daylio_to_md import utils, errors
from daylio_to_md.config import options
from daylio_to_md.entry.mood import Moodverse

"""---------------------------------------------------------------------------------------------------------------------
ADD SETTINGS SPECIFIC TO JOURNAL ENTRIES TO ARGPARSE
---------------------------------------------------------------------------------------------------------------------"""
# Adding DatedEntry-specific options in global_settings
journal_entry_settings = options.arg_console.add_argument_group(
    "Journal entry settings",
    "Handles how journal entries should be formatted"
)
journal_entry_settings.add_argument(
    "--tags",
    help="Tags in the YAML of each note.",
    nargs='*',  # this allows, for example, "--tags one two three" --> ["one", "two", "three"]
    default="daily",
    dest="TAGS"
)
journal_entry_settings.add_argument(
    "--prefix",  # <here's your prefix>YYYY-MM-DD.md so remember about a separating char
    default='',
    help="Prepends a given string to each entry's header."
)
journal_entry_settings.add_argument(
    "--suffix",  # YYYY-MM-DD<here's your suffix>.md so remember about a separating char
    default='',
    help="Appends a given string at the end of each entry's header."
)
journal_entry_settings.add_argument(
    "--tag_activities", "-a",
    action="store_true",  # default=True
    help="Tries to convert activities into valid tags.",
    dest="ACTIVITIES_AS_TAGS"
)
journal_entry_settings.add_argument(
    "-colour", "--color",
    action="store_true",  # default=True
    help="Prepends a colour emoji to each entry depending on mood.",
    dest="colour"
)
journal_entry_settings.add_argument(
    "--header",
    type=int,
    default=2,
    help="Headings level for each entry.",
    dest="HEADER_LEVEL"
)
journal_entry_settings.add_argument(
    "--csv-delimiter",
    default="|",
    help="Set delimiter for activities in Daylio .CSV, e.g: football | chess"
)

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
class BaseEntryConfig:
    """Stores information on how to build and configurate a :class:`DatedEntry`."""
    csv_delimiter: str = '|'
    header_multiplier: int = 2
    tag_activities: bool = True


class Entry(utils.Core):
    """
    Journal entry

    :param time: Time at which this note was created. It will be type-casted into :class:`datetime.time` object.
    :param mood: Mood felt during writing this note.
                 It can be any :class:`str`, but during output the colouring won't work if the mood is not recognised.
                 (i.e `joyful` won't appear green if it isn't in the ``moods.json``)
    :param activities: (opt.) Activities carried out around or at the time of writing the note
    :param title: (opt.) Title of the note
    :param note: (opt.) The contents of the journal note itself
    :param config: (opt). Configures how an entry should be processed or outputted
    :param mood_set: (opt.) Set if you want to use custom :class:`Moodverse` for mood handling
    :raise InvalidTimeError: if the passed time argument cannot be coerced into :class:`datetime.time`
    :raise NoMoorError: if mood is falsy
    """

    def __init__(self,
                 time: typing.Union[datetime.time, str, typing.List[int], typing.List[int]],
                 mood: str,
                 activities: str = None,
                 title: str = None,
                 note: str = None,
                 config: BaseEntryConfig = BaseEntryConfig(),
                 mood_set: Moodverse = Moodverse()):

        # TODO: have to test the whole instantiation function again after refactoring
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.config = config

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
            working_array = utils.strip_and_get_truthy(activities, config.csv_delimiter)
            if len(working_array) > 0:
                for activity in working_array:
                    self.__activities.append(utils.slugify(
                        activity,
                        config.tag_activities
                    ))
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
            self.config.header_multiplier * "#" + ' ' + self.__mood,
            self.time.strftime("%H:%M"),
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
