import datetime
from unittest import TestCase

import tests.suppress as suppress
from daylio_to_md.utils import InvalidTimeError
from daylio_to_md.journal_entry import \
    Entry, \
    BaseEntryConfig, \
    NoMoodError


class TestJournalEntry(TestCase):
    @suppress.out
    def test_bare_minimum_journal_entries(self):
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

    @suppress.out
    def test_other_variants_of_journal_entries(self):
        # When
        entry = Entry(
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
        entry = Entry(
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
        tag_my_activities = BaseEntryConfig(tag_activities=True)
        entry = Entry(
            time="1:49 AM",
            mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred.",
            activities="bicycle|chess|gaming",
            config=tag_my_activities
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(1, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertEqual("A completely normal situation just occurred.", entry.note)
        self.assertListEqual(["#bicycle", "#chess", "#gaming"], entry.activities)

        # When
        do_not_tag_my_activities = BaseEntryConfig(tag_activities=False)
        entry = Entry(
            time="3:49 PM",
            mood="vaguely ok",
            title="Normal situation",
            note="A completely normal situation just occurred.",
            activities="bicycle|chess|gaming",
            config=do_not_tag_my_activities
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(15, 49), entry.time)
        self.assertEqual("Normal situation", entry.title)
        self.assertEqual("A completely normal situation just occurred.", entry.note)
        self.assertListEqual(["bicycle", "chess", "gaming"], entry.activities)

    @suppress.out
    def test_insufficient_journal_entries(self):
        self.assertRaises(NoMoodError, Entry, time="2:00", mood="")
        self.assertRaises(InvalidTimeError, Entry, time=":00", mood="vaguely ok")

    @suppress.out
    def test_entries_with_weird_activity_lists(self):
        # When
        tag_my_activities = BaseEntryConfig(tag_activities=True)
        entry = Entry(
            time="11:49 PM",
            mood="vaguely ok",
            activities="||bicycle|@Q$@$Q''\"chess|gaming-+/$@q4%#!!",
            config=tag_my_activities
        )

        # Then
        self.assertEqual("vaguely ok", entry.mood)
        self.assertEqual(datetime.time(23, 49), entry.time)
        self.assertIsNone(entry.title)
        self.assertIsNone(entry.note)
        self.assertListEqual(['#bicycle', '#qqchess', '#gaming-q4'], entry.activities)
