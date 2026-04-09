"""Integration tests for the Reader → Librarian → Journal pipeline."""
import pytest

from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.group import EntriesFromBuilder
from obsidian_daylio_parser.journal_entry import EntryBuilder
from obsidian_daylio_parser.librarian import Librarian, CannotAccessJournalError
from obsidian_daylio_parser.reader import CsvJournalReader


class TestParsing:
    def test_valid_csv(self, parsed_journal):
        assert parsed_journal

    @pytest.mark.parametrize("path", [
        "tests/files/scenarios/fail/corrupted.csv",
        "tests/files/scenarios/fail/wrong-format.txt",
        "tests/files/fail/missing.csv",
    ])
    def test_invalid_sources_raise(self, path):
        with pytest.raises(CannotAccessJournalError):
            Librarian(CsvJournalReader(path)).parse()


class TestJournalAccess:
    @pytest.mark.parametrize("date", ["2022-10-25", "2022-10-26", "2022-10-27", "2022-10-30"])
    def test_valid_dates_accessible(self, parsed_journal, date):
        assert parsed_journal[date]

    @pytest.mark.parametrize("date", ["2022-10-21", "2022-10-20", "2022-10-2", "1999-10-22"])
    def test_missing_dates_raise_key_error(self, parsed_journal, date):
        with pytest.raises(KeyError):
            parsed_journal[date]

    @pytest.mark.parametrize("bad_key", ["ABC", "2022", "12:00 AM"])
    def test_invalid_keys_raise_value_error(self, parsed_journal, bad_key):
        with pytest.raises(ValueError):
            parsed_journal[bad_key]


class TestMoodLoading:
    def test_custom_moods_loaded(self, ok_csv, fixtures_path):
        mood_set = Moodverse.from_file(str(fixtures_path / "all-valid.json"))
        journal = Librarian(CsvJournalReader(str(ok_csv)), mood_set).parse()
        assert journal.mood_set.get_custom_moods

    def test_no_custom_moods_by_default(self, parsed_journal):
        assert len(parsed_journal.mood_set.get_custom_moods) == 0

    def test_invalid_json_falls_back_to_defaults(self, ok_csv, fixtures_path):
        mood_set = Moodverse.from_file(str(fixtures_path / "scenarios" / "fail" / "empty.csv"))
        journal = Librarian(CsvJournalReader(str(ok_csv)), mood_set).parse()
        assert journal.mood_set.get_moods == Moodverse().get_moods

    def test_incomplete_json_loads_partial_customs(self, fixtures_path):
        reader = CsvJournalReader(str(fixtures_path / "scenarios" / "ok" / "all-valid.csv"))
        mood_set = Moodverse.from_file(str(fixtures_path / "moods" / "incomplete.json"))
        config = EntriesFromBuilder(entries_builder=EntryBuilder(tag_activities=True))
        journal = Librarian(reader, mood_set, config).parse()
        assert len(journal.mood_set.get_custom_moods) == 10
