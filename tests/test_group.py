"""Unit tests for EntriesFrom — date grouping, entry access, and day-level markdown output."""
import datetime
import io

import pytest

from obsidian_daylio_parser.group import EntriesFrom, EntryMissingError, IncompleteDataRow
from obsidian_daylio_parser.journal_entry import Entry
from obsidian_daylio_parser.utils import InvalidDateError, InvalidTimeError


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------
class TestDateParsing:
    @pytest.mark.parametrize(tuple("raw, expected_str"), [
        ("2023-10-15", "2023-10-15"),
        ("2019-5-9", "2019-05-09"),
        ("2023-11-25", "2023-11-25"),
    ])
    def test_valid_dates(self, raw, expected_str):
        assert str(EntriesFrom(raw)) == expected_str

    def test_date_property(self):
        assert EntriesFrom("2023-10-15").date == datetime.date(2023, 10, 15)

    def test_whitespace_trimmed(self):
        assert EntriesFrom("   2022-05-18  ").date == datetime.date(2022, 5, 18)

    @pytest.mark.parametrize("raw", [
        "00-", "2199-32-32",
        "2022/05/18", "2023_07_12", "1999.10.25",
        "2@#0$2-05-18", "1987-0%4-12", "2001-07-3*",
        "1999- 10-25", "  2000-04 -  12  ",
        "2k20-05-18", "1999-0ne-25", "2021-07-Two",
        "2022-05", "1987-09", "2001", "",
    ])
    def test_invalid_dates(self, raw):
        with pytest.raises(InvalidDateError):
            EntriesFrom(raw)


# ---------------------------------------------------------------------------
# Entry access
# ---------------------------------------------------------------------------
class TestEntryAccess:
    def test_access_by_time_string(self, sample_day):
        assert str(sample_day["9:30 PM"]) == "21:30"
        assert sample_day["10:00 AM"].time == datetime.time(10, 0)

    @pytest.mark.parametrize("bad_time", [
        "2: AM", "15:45 PM", "14:45 PM", "11:30 XM", "03:20 XM",
        "25:15", "11:78", "/ASDFVDJU\\", "2022-1", "12:", ":30",
    ])
    def test_invalid_time_access_raises(self, sample_day, bad_time):
        with pytest.raises(InvalidTimeError):
            sample_day[bad_time]

    def test_missing_entry_raises(self, sample_day):
        with pytest.raises(KeyError):
            sample_day["23:00"]
        with pytest.raises(EntryMissingError):
            sample_day["11:50 AM"]


# ---------------------------------------------------------------------------
# Creating entries from CSV row dicts
# ---------------------------------------------------------------------------
class TestCreateEntry:
    def test_valid_row(self):
        day = EntriesFrom("1999-05-07")
        day.create_entry({
            "time": "10:00 AM", "mood": "vaguely ok",
            "activities": "", "note_title": "", "note": "",
        })
        assert len(day.known_entries) == 1

    def test_missing_mood_raises(self):
        day = EntriesFrom("1999-05-07")
        with pytest.raises(IncompleteDataRow):
            day.create_entry({
                "time": "5:00 PM", "mood": "",
                "activities": "", "note_title": "", "note": "",
            })

    def test_duplicate_allowed(self, sample_day):
        """Daylio allows duplicate timestamps — no error should be raised."""
        sample_day.create_entry({
            "time": "10:00 AM", "mood": "vaguely ok",
            "activities": "", "note_title": "", "note": "",
        })


# ---------------------------------------------------------------------------
# Truthiness / identity
# ---------------------------------------------------------------------------
class TestGroupProperties:
    def test_truthy_when_has_entries(self, sample_day):
        assert len(sample_day.known_entries) > 0

    def test_falsy_when_empty(self):
        assert not EntriesFrom("2019-09-12").known_entries

    def test_same_date_independent_instances(self):
        assert EntriesFrom("2020-01-01") is not EntriesFrom("2020-01-01")


# ---------------------------------------------------------------------------
# Day-level markdown output
# ---------------------------------------------------------------------------
class TestEntriesFromOutput:
    @staticmethod
    def _render(day: EntriesFrom) -> str:
        buf = io.StringIO()
        day.output(buf)
        return buf.getvalue()

    def test_single_entry(self):
        day = EntriesFrom("2011-10-10")
        day.add(Entry(time="10:00 AM", mood="vaguely ok"))
        expected = (
            "---\ntags: daylio\n---\n\n"
            "## vaguely ok | 10:00\n\n"
        )
        assert self._render(day) == expected

    def test_two_entries(self):
        day = EntriesFrom("2011-10-10")
        day.add(
            Entry(time="10:00 AM", mood="vaguely ok", activities="bowling", note="Feeling kinda ok."),
            Entry(time="9:30 PM", mood="awful", title="Everything is going downhill for me"),
        )
        expected = (
            "---\ntags: daylio\n---\n\n"
            "## vaguely ok | 10:00\n#bowling\nFeeling kinda ok.\n\n"
            "## awful | 21:30 | Everything is going downhill for me\n\n"
        )
        assert self._render(day) == expected

    def test_all_invalid_tags_omits_frontmatter(self):
        day = EntriesFrom("2011-10-10", front_matter_tags=["", None])
        day.add(
            Entry(time="10:00 AM", mood="vaguely ok", activities="bowling", note="Feeling kinda meh."),
            Entry(time="9:30 PM", mood="awful", title="Everything is going downhill for me"),
        )
        result = self._render(day)
        assert not result.startswith("---")

    def test_partially_valid_tags(self):
        day = EntriesFrom("2011-10-10", front_matter_tags=["", "foo", "bar", None])
        day.add(
            Entry(time="10:00 AM", mood="vaguely ok", activities="bowling", note="Feeling fine, I guess."),
            Entry(time="9:30 PM", mood="awful", title="Everything is going downhill for me"),
        )
        result = self._render(day)
        assert result.startswith("---\ntags: bar,foo\n---\n\n")
