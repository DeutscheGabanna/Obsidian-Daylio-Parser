import datetime
from unittest import TestCase

from daylio_to_md.utils import InvalidTimeError
from daylio_to_md.journal_entry import \
    Entry, \
    EntryBuilder, \
    NoMoodError


class TestJournalEntry(TestCase):
    def test_bare_minimum_journal_entries_as_standalone_class(self):
        # When
        bare_minimum_entry = Entry(
            time="1:49 AM",
            mood="vaguely ok"
        )

        # Then
        self.assertEqual("vaguely ok", bare_minimum_entry.mood)
        self.assertEqual(datetime.time(1, 49), bare_minimum_entry.time)
        self.assertIsNone(bare_minimum_entry.title)
        self.assertIsNone(bare_minimum_entry.note)
        self.assertListEqual([], bare_minimum_entry.activities)

    def test_bare_minimum_journal_entries_from_builder_class(self):
        # When
        bare_minimum_entry = EntryBuilder().build(
            time="1:49 AM",
            mood="vaguely ok"
        )

        # Then
        self.assertEqual("vaguely ok", bare_minimum_entry.mood)
        self.assertEqual(datetime.time(1, 49), bare_minimum_entry.time)
        self.assertIsNone(bare_minimum_entry.title)
        self.assertIsNone(bare_minimum_entry.note)
        self.assertListEqual([], bare_minimum_entry.activities)

    def test_other_variants_of_journal_entries(self):
        # When
        entry = EntryBuilder().build(
            time="1:49 AM",
            mood="vaguely ok",
            title="Normal situation"
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(1, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertIsNone(entry.note)
        self.assertListEqual([], entry.activities)

        # When
        entry = EntryBuilder().build(
            time="1:49 AM",
            mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred."
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(1, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertEqual("A completely normal situation just occurred.", entry.note)
        self.assertListEqual([], entry.activities)

        # When
        entry = EntryBuilder(tag_activities=True).build(
            time="1:49 AM",
            mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred.",
            activities="bicycle|chess|gaming"
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(1, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertEqual("A completely normal situation just occurred.", entry.note)
        self.assertListEqual(["#bicycle", "#chess", "#gaming"], entry.activities)

        # When
        entry = EntryBuilder(tag_activities=False).build(
            time="3:49 PM",
            mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred.",
            activities="bicycle|chess|gaming"
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(15, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertEqual("A completely normal situation just occurred.", entry.note)
        self.assertListEqual(["bicycle", "chess", "gaming"], entry.activities)

    def test_insufficient_journal_entries(self):
        self.assertRaises(NoMoodError, Entry, time="2:00", mood="")
        self.assertRaises(InvalidTimeError, Entry, time=":00", mood="vaguely ok")

    def test_entries_with_weird_activity_lists(self):
        # When
        entry = Entry(
            time="11:49 PM",
            mood="vaguely ok",
            activities="||bicycle|@Q$@$Q''\"chess|gaming-+/$@q4%#!!"
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(23, 49), entry.time)
        self.assertIsNone(entry.title)
        self.assertIsNone(entry.note)
        self.assertListEqual(['#bicycle', '#qqchess', '#gaming-q4'], entry.activities)
