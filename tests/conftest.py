"""
Shared pytest fixtures for the obsidian-daylio-parser test suite.

These fixtures provide reusable building blocks so individual test modules
don't have to repeat the same setup boilerplate.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.group import EntriesFrom
from obsidian_daylio_parser.journal_entry import Entry
from obsidian_daylio_parser.librarian import Librarian
from obsidian_daylio_parser.reader import CsvJournalReader

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

FILES = Path(__file__).parent / "files"


@pytest.fixture
def resources_path() -> Path:
    return FILES


@pytest.fixture
def ok_csv() -> Path:
    return FILES / f"daylio_export_ok.csv"


@pytest.fixture
def ok_expected_dir() -> Path:
    return FILES / "golden_files"


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------


@pytest.fixture
def default_moodverse() -> Moodverse:
    """The five built-in Daylio moods with no custom additions."""
    return Moodverse()


@pytest.fixture
def custom_moodverse() -> Moodverse:
    """Moodverse loaded from the full test JSON (all-valid.json)."""
    return Moodverse.from_file(FILES / "moods_ok_custom.json")


@pytest.fixture
def sample_entry() -> Entry:
    """A minimal valid entry: time + mood only."""
    return Entry(time="11:00", mood="great")


@pytest.fixture
def sample_day() -> EntriesFrom:
    """A day (2011-10-10) preloaded with two entries."""
    day = EntriesFrom("2011-10-10")
    day.add(
        Entry(time="10:00 AM", mood="vaguely ok"),
        Entry(time="9:30 PM", mood="awful"),
    )
    return day


@pytest.fixture
def parsed_journal(ok_csv):
    """Journal parsed from the OK scenario CSV with default moods."""
    reader = CsvJournalReader(ok_csv)
    return Librarian(reader).parse()
