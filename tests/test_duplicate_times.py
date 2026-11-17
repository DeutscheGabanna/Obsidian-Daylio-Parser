"""Synthetic records with nonunique timestamps must survive parsing and output."""
import datetime

import pytest

from obsidian_daylio_parser.group import EntryMissingError
from obsidian_daylio_parser.librarian import Librarian
from obsidian_daylio_parser.reader import CsvJournalReader
from obsidian_daylio_parser.writer import MarkdownWriter


@pytest.fixture
def collision_journal(resources_path):
    return Librarian(CsvJournalReader(resources_path / "daylio_export_duplicate_times.csv")).parse()


def test_two_entries_at_same_time(resources_path):
    source = resources_path / "daylio_export_two_same_time.csv"
    journal = Librarian(CsvJournalReader(source)).parse()
    assert len(journal) == 2
    assert [entry.note for entry in journal["2022-10-30"]] == ["First record", "Second record"]


def test_multiple_collisions_preserve_csv_order_and_dates(collision_journal):
    assert len(collision_journal) == 6
    assert collision_journal.dates == [datetime.date(2022, 10, 30), datetime.date(2022, 10, 31)]
    day = collision_journal["2022-10-30"]
    assert len(day) == 5
    assert [entry.title for entry in day] == [
        "First collision", "Earlier time", "Second collision", "Later time", "Third collision",
    ]
    assert len(collision_journal["2022-10-31"]) == 1


@pytest.mark.parametrize("key", ["20:00", "8:00 PM", datetime.time(20), [20, 0]])
def test_time_lookup_returns_all_matches_in_order(collision_journal, key):
    day = collision_journal["2022-10-30"]
    matches = day[key]
    assert isinstance(matches, tuple)
    assert [entry.title for entry in matches] == ["First collision", "Second collision", "Third collision"]
    assert day.known_entries[datetime.time(20)] == matches
    assert len(day["08:00"]) == 1
    with pytest.raises(EntryMissingError):
        day["09:00"]


def test_markdown_contains_every_record_in_csv_order(collision_journal, tmp_path):
    MarkdownWriter(tmp_path).write_all(collision_journal)
    markdown = (tmp_path / "2022/10/2022-10-30.md").read_text(encoding="utf-8")
    titles = ["First collision", "Earlier time", "Second collision", "Later time", "Third collision"]
    assert all(markdown.count(title) == 1 for title in titles)
    assert [markdown.index(title) for title in titles] == sorted(markdown.index(title) for title in titles)
    assert "Other date" in (tmp_path / "2022/10/2022-10-31.md").read_text(encoding="utf-8")


@pytest.fixture
def two_entry_day(resources_path):
    journal = Librarian(CsvJournalReader(resources_path / "daylio_export_two_same_time.csv")).parse()
    return journal["2022-10-30"]


def test_add_preserves_existing_entries_at_same_time(two_entry_day, collision_journal):
    additional_entry = collision_journal["2022-10-30"]["20:00"][0]

    two_entry_day.add(additional_entry)

    assert len(two_entry_day) == 3
    assert [entry.note for entry in two_entry_day] == [
        "First record", "Second record", "Synthetic record one.",
    ]
    assert [entry.note for entry in two_entry_day["20:00"]] == [
        "First record", "Second record", "Synthetic record one.",
    ]


def test_time_assignment_preserves_existing_entries_at_same_time(two_entry_day, collision_journal):
    additional_entry = collision_journal["2022-10-30"]["20:00"][0]

    two_entry_day["20:00"] = additional_entry

    assert len(two_entry_day) == 3
    assert [entry.note for entry in two_entry_day] == [
        "First record", "Second record", "Synthetic record one.",
    ]
    assert [entry.note for entry in two_entry_day["20:00"]] == [
        "First record", "Second record", "Synthetic record one.",
    ]
