"""
This file specialises in building the middleware between actual journal entries and the whole journal.
It creates and organises only those entries written on a particular date. This way they can be handled easier.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
all notes -> _NOTES WRITTEN ON A PARTICULAR DATE_ -> a particular note
"""
from __future__ import annotations
from dataclasses import dataclass, field

import io
import typing
import logging
import datetime

from daylio_to_md import journal_entry
from daylio_to_md import utils, errors
from daylio_to_md.config import DEFAULTS
from daylio_to_md.journal_entry import Entry
from daylio_to_md.entry.mood import Moodverse

# TODO: dependency_injector lib
# TODO: fixtures


"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class EntryMissingError(KeyError):
    """The entry written at {key} does not exist in the dictionary of known entries from {date}."""
    def __init__(self, key, date):
        self.__doc__ = self.__doc__.format(key=key, date=date)
        super().__init__()


class IncompleteDataRow(Exception):
    """Passed a row of data from CSV file that does not have all required fields."""


class TriedCreatingDuplicateDatedEntryError(Exception):
    """Tried to create object of :class:`DatedEntry` that would be a duplicate of one that already exists."""


class ErrorMsg(errors.ErrorMsgBase):
    CSV_ROW_INCOMPLETE_DATA = "Passed .csv contains rows with invalid data. Tried to parse {} as date."


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


@dataclass(frozen=True)
class EntriesFromBuilder:
    """
    Configure one instance of this, and you won't have to provide the same configuration
    over and over again when it instantiates new :class:`EntriesFrom` objects for you.
    :param front_matter_tags: Tags in the YAML front-matter of each note
    :param entries_builder: Builder configured to create new :class:`Entry` objects
    """
    front_matter_tags: tuple[str] = DEFAULTS.frontmatter_tags
    entries_builder: journal_entry.EntryBuilder = field(default_factory=journal_entry.EntryBuilder)

    def build(self,
              date: typing.Union[datetime.date, str, typing.List[str], typing.List[int]],
              mood_set: Moodverse = Moodverse()) -> EntriesFrom:

        return EntriesFrom(
            utils.guess_date_type(date),
            self.front_matter_tags,
            self.entries_builder,
            mood_set
        )


class EntriesFrom(utils.Core):
    """
    A group of entries written on the same day.

    :raises InvalidDateError: if the date cannot be type cast into :class:`datetime.date`
    :param date: The date for all child entries within. Always type-casted into :class:`datetime.date`
    :param front_matter_tags: Tags in the YAML front-matter of each note
    :param entries_builder: Builder configured to create new :class:`Entry` objects
    :param mood_set: Use custom :class:`Moodverse` or default if not provided.
    """
    _instances: dict[datetime.date, EntriesFrom] = {}

    def __new__(cls,
                date: typing.Union[datetime.date, str, typing.List[str], typing.List[int]],
                *args,
                **kwargs):

        type_casted_date = utils.guess_date_type(date)

        # Check if an instance for the given date already exists
        if type_casted_date in cls._instances:
            return cls._instances[type_casted_date]

        # If not, create a new instance
        instance = super(EntriesFrom, cls).__new__(cls)
        cls._instances[type_casted_date] = instance

        return instance

    def __init__(self,
                 date: typing.Union[datetime.date, str, typing.List[str], typing.List[int]],
                 front_matter_tags: tuple[str] = EntriesFromBuilder.front_matter_tags,
                 entries_builder: journal_entry.EntryBuilder = journal_entry.EntryBuilder(),
                 mood_set: Moodverse = Moodverse()):

        self.__logger = logging.getLogger(self.__class__.__name__)
        super().__init__(utils.guess_date_type(date))

        # All good - initialise
        self.__front_matter_tags = front_matter_tags
        self.__entries_builder = entries_builder
        self.__known_entries: dict[datetime.time, Entry] = {}
        self.__known_moods: Moodverse = mood_set

    def create_entry(self, line: dict[str, str]) -> None:
        """
        Create :class:`Entry` object with the specified parameters.
        Field with date is ignored, because :class:`Entry` inherits this field from parent :class:`EntriesFrom`.
        The assumption here is that .create_entry() should never be called for an entry from a different date.
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

        # TODO: date mismatch - this object has a different date than the full_date in line

        # Instantiate the entry
        time = utils.guess_time_type(line["time"])
        self[time] = self.__entries_builder.build(
            time,
            line["mood"],
            line["activities"],
            line["note_title"],
            line["note"],
            mood_set=self.__known_moods,
        )

    def __getitem__(self, item: typing.Union[datetime.time, str, typing.List[int], typing.List[str]]) -> Entry:
        """
        Retrieve an already existing :class:`Entry` object.
        e.g::

            my_entries["10:00 AM"]
            my_entries[10, 0]
            my_entries[datetime.time(10, 3)]

        :param item: value that can be type-casted into a valid :class:`datetime.time` object
        :raises EntryMissingError: if the entry specified in ``time`` does not exist
        :returns: :class:`DatedEntry`
        """
        time_lookup: datetime.time = utils.guess_time_type(item)

        if time_lookup in self.__known_entries:
            return self.__known_entries[time_lookup]
        else:
            raise EntryMissingError(time_lookup, self.date)

    def __setitem__(self, key: typing.Union[datetime.time, str, typing.List[int], typing.List[str]], value: Entry):
        """
        :param key: any of the three types that can be type-casted into valid :class:`datetime.time` object
        :param value: :class:`Entry` object
        :raise TypeError: if key cannot be coerced into proper object type or there is a type mismatch
        """
        if not isinstance(value, Entry):
            raise TypeError("Trying to assign {value} of type {type} as entry for {date}".format(
                value=value,
                type=type(value),
                date=self.date
            ))
        time = utils.guess_time_type(key)
        self.__known_entries[time] = value

    def add(self, *args: Entry) -> None:
        """
        Add all *args into the list of known entries written on that day.
        :param args: one or more :class:`Entry` objects to add
        """
        for item in args:
            if not isinstance(item, Entry):
                continue
            self[item.time] = item

    def output(self, stream: io.IOBase | typing.IO) -> int:
        """
        Write entry contents of all :class:`Entry` known directly into the provided buffer stream.
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
        # when appending file frontmatter_tags at the beginning of the file, discard any duplicates or falsy strings
        # sorted() is used to have a deterministic order, set() was random, so I couldn't properly test the output
        valid_tags = sorted(set(val for val in self.__front_matter_tags if val))
        if valid_tags:
            # why '\n' instead of os.linesep?
            # > Do not use os.linesep as a line terminator when writing files opened in text mode (the default);
            # > use a single '\n' instead, on all platforms.
            # https://docs.python.org/3.10/library/os.html#os.linesep
            chars_written += stream.write("---" + "\n")
            chars_written += stream.write("frontmatter_tags: " + ",".join(valid_tags) + "\n")
            chars_written += stream.write("---" + "\n" * 2)

        # THE ACTUAL ENTRY CONTENTS
        # Each DatedEntry object now appends its contents into the stream
        for entry in self.__known_entries.values():
            # write returns the number of characters successfully written
            # https://docs.python.org/3/library/io.html#io.TextIOBase.write
            if entry.output(stream) > 0:
                chars_written += stream.write("\n" * 2)

        return chars_written

    @property
    def known_entries(self):
        return self.__known_entries

    @property
    def date(self):
        """
        :return: :class:`datetime.date` object that identifies this instance of :class:`EntriesFrom`.
        """
        return self.uid

    def __eq__(self, other) -> bool:
        """Enables direct comparison with a :class:`datetime.date` or a date string. """
        # TODO: check if all known entries match as well, this date check is too superfluous right now
        if isinstance(other, EntriesFrom):
            return all([
                self.date == other.date,
                self.known_entries == other.known_entries
            ])
        return super().__eq__(other)

    def __str__(self):
        """:return: the date that groups entries written on that day in ``YYYY-MM-DD`` format"""
        return self.uid.strftime("%Y-%m-%d")
