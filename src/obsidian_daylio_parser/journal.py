"""
The parsed journal — a date-indexed collection of entry groups.
This is the product of :class:`Librarian.parse`. It holds the data, but owns none of the parsing or output logic.

└── **Journal**
 └── EntriesFrom (a particular date)
  └── Entry (a particular moment)
"""
from __future__ import annotations

import datetime
import typing

from obsidian_daylio_parser.group import EntriesFrom
from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.utils import guess_date_type


class Journal:
    """
    Immutable-ish result of parsing a journal source.
    Holds a ``date -> EntriesFrom`` mapping and supports dict-like access by date string, datetime.date, or list.

    Usage::

        journal = Librarian(reader, mood_set).parse()
        journal["2022-10-25"]               # access by date string
        journal[datetime.date(2022, 10, 25)] # access by datetime.date
        for entries_from in journal:         # iterate over all days
            ...
    """

    def __init__(self, entries_by_date: dict[datetime.date, EntriesFrom], mood_set: Moodverse):
        self.__entries = dict(entries_by_date)  # defensive copy
        self.__mood_set = mood_set

    def __getitem__(self, key: typing.Union[datetime.date, str, typing.List[str], typing.List[int]]) -> EntriesFrom:
        """
        Access an :class:`EntriesFrom` for the specified date.

        e.g.::

            journal[datetime.date(2022, 10, 10)]
            journal["2022-10-10"]
            journal[[2022, 10, 10]]

        :raises KeyError: if key cannot be found in the dictionary of known dates.
        :return: :class:`EntriesFrom` object for that date.
        """
        date = guess_date_type(key)
        if date in self.__entries:
            return self.__entries[date]
        raise KeyError(f"No entries for {date}")

    def __iter__(self):
        """Iterate over all :class:`EntriesFrom` groups in the journal."""
        return iter(self.__entries.values())

    def __len__(self):
        """Total number of individual entries across all dates."""
        return sum(len(group) for group in self.__entries.values())

    def __bool__(self):
        return len(self.__entries) > 0

    @property
    def dates(self) -> list[datetime.date]:
        """All dates for which the journal has entries."""
        return list(self.__entries.keys())

    @property
    def mood_set(self) -> Moodverse:
        """The :class:`Moodverse` that was used to parse this journal."""
        return self.__mood_set

    def __repr__(self):
        total = sum(len(g) for g in self.__entries.values())
        dates = [str(d) for d in self.__entries.keys()]
        return f"Journal(dates={dates}, total_entries={total})"
