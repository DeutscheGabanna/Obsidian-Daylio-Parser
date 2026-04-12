"""Unit tests for Entry — construction, validation, and markdown output."""
import datetime
import io

import pytest

from obsidian_daylio_parser.journal_entry import Entry, EntryBuilder, NoMoodError
from obsidian_daylio_parser.utils import InvalidTimeError


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------
class TestEntryConstruction:
    def test_bare_minimum(self):
        e = Entry(time="1:49 AM", mood="vaguely ok")
        assert e.mood == "vaguely ok"
        assert e.time == datetime.time(1, 49)
        assert e.title is None
        assert e.note is None
        assert e.scales == []
        assert e.activities == []

    def test_via_builder(self):
        e = EntryBuilder().build(time="1:49 AM", mood="vaguely ok")
        assert e.mood == "vaguely ok"
        assert e.time == datetime.time(1, 49)

    def test_with_title(self):
        e = EntryBuilder().build(time="1:49 AM", mood="vaguely ok", title="Normal situation")
        assert e.title == "Normal situation"
        assert e.note is None

    def test_with_all_fields(self):
        e = EntryBuilder().build(
            time="1:49 AM", mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred.",
        )
        assert e.note == "A completely normal situation just occurred."

    def test_activities_tagged(self):
        e = EntryBuilder(tag_activities=True).build(
            time="1:49 AM", mood="vaguely ok", activities="bicycle|chess|gaming",
        )
        assert e.activities == ["#bicycle", "#chess", "#gaming"]

    def test_activities_untagged(self):
        e = EntryBuilder(tag_activities=False).build(
            time="3:49 PM", mood="vaguely ok", activities="bicycle|chess|gaming",
        )
        assert e.activities == ["bicycle", "chess", "gaming"]

    def test_weird_activity_strings(self):
        e = Entry(
            time="11:49 PM", mood="vaguely ok",
            activities='||bicycle|@Q$@$Q\'\'"chess|gaming-+/$@q4%#!!',
        )
        assert e.activities == ["#bicycle", "#qqchess", "#gaming-q4"]

    def test_scales(self):
        e = Entry(
            time="10:05 PM", mood="great",
            scales='Sleep Quality: 4/10 points | Sleep Time: 7:00'
        )
        assert e.scales == ["Sleep Quality: 4/10 points", "Sleep Time: 7:00"]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
class TestEntryValidation:
    def test_empty_mood_raises(self):
        with pytest.raises(NoMoodError):
            Entry(time="2:00", mood="")

    def test_invalid_time_raises(self):
        with pytest.raises(InvalidTimeError):
            Entry(time=":00", mood="vaguely ok")


# ---------------------------------------------------------------------------
# Output (Markdown rendering of a single entry)
# ---------------------------------------------------------------------------
class TestEntryOutput:
    @staticmethod
    def _render(entry: Entry) -> str:
        buf = io.StringIO()
        entry.output(buf)
        return buf.getvalue()

    def test_mood_and_time_only(self):
        result = self._render(Entry(time="11:00", mood="great", activities="bicycle | chess"))
        assert result == "## great | 11:00\n#bicycle #chess"

    def test_with_title_no_note(self):
        result = self._render(Entry(
            time="11:00", mood="great", activities="bicycle | chess", title="I'm super pumped!",
        ))
        assert result == "## great | 11:00 | I'm super pumped!\n#bicycle #chess"

    def test_with_title_and_note(self):
        result = self._render(Entry(
            time="11:00", mood="great", activities="bicycle | chess",
            title="I'm super pumped!",
            note="I believe I can fly, I believe I can touch the sky.",
        ))
        expected = (
            "## great | 11:00 | I'm super pumped!\n"
            "#bicycle #chess\n"
            "I believe I can fly, I believe I can touch the sky."
        )
        assert result == expected

    def test_tagged_vs_untagged_activities_with_builder(self):
        tagged = self._render(EntryBuilder(tag_activities=True).build(
            time="11:00", mood="great", activities="bicycle | chess",
        ))
        assert "#bicycle #chess" in tagged

        untagged = self._render(EntryBuilder(tag_activities=False).build(
            time="11:00", mood="great", activities="bicycle | chess",
        ))
        assert "bicycle chess" in untagged

    def test_tagged_vs_untagged_activities_without_builder(self):
        tagged = self._render(Entry(time="11:00", mood="great", activities="bicycle | chess"))
        assert "#bicycle #chess" in tagged

        untagged = self._render(Entry(
            time="11:00", mood="great", activities="bicycle | chess", tag_activities=False,
        ))
        assert "bicycle chess" in untagged

    def test_header_multiplier_with_builder(self):
        result = self._render(EntryBuilder(header_multiplier=5).build(
            time="11:00", mood="great", title="Feeling pumped@!"
        ))
        assert result == "##### great | 11:00 | Feeling pumped@!"

    def test_header_multiplier_without_builder(self):
        result = self._render(Entry(
            time="11:00", mood="great", title="Feeling pumped@!", header_multiplier=5
        ))
        assert result == "##### great | 11:00 | Feeling pumped@!"
