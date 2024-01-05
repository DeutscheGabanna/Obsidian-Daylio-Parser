from unittest import TestCase
from dated_entry import Time, slice_quotes, DatedEntry, IsNotTimeError


class TestDatedEntryUtils(TestCase):
    def test_slice_quotes(self):
        self.assertEqual(slice_quotes("\"test\""), "test")
        self.assertEqual(slice_quotes("\"\""), "")


class TestTime(TestCase):
    def test_try_creating_valid_times(self):
        # Valid time formats
        self.assertTrue(Time("1:49 AM"))
        self.assertTrue(Time("02:15 AM"))
        self.assertTrue(Time("12:00 PM"))
        self.assertTrue(Time("6:30 PM"))
        self.assertTrue(Time("9:45 PM"))
        self.assertTrue(Time("00:00 AM"))
        self.assertTrue(Time("12:00 AM"))
        self.assertTrue(Time("13:30"))
        self.assertTrue(Time("9:45"))

    def test_try_creating_invalid_times(self):
        # Invalid time formats
        # noinspection SpellCheckingInspection
        self.assertRaises(IsNotTimeError, Time, "okk:oksdf s")
        self.assertRaises(IsNotTimeError, Time, "14:59 AM")
        self.assertRaises(IsNotTimeError, Time, "25:00 AM")
        self.assertRaises(IsNotTimeError, Time, "26:10")
        self.assertRaises(IsNotTimeError, Time, "12:60 PM")
        self.assertRaises(IsNotTimeError, Time, "12:00 XX")
        self.assertRaises(IsNotTimeError, Time, "abc:def AM")
        self.assertRaises(IsNotTimeError, Time, "24:00 PM")
        self.assertRaises(IsNotTimeError, Time, "00:61 AM")


class TestDatedEntry(TestCase):
    def test_bare_minimum_dated_entries(self):
        # When
        bare_minimum_dated_entry = DatedEntry(
            time="1:49 AM",
            mood="vaguely ok",
            known_moods={
                "neutral": ["vaguely ok"]
            }
        )

        # Then
        self.assertTrue(bare_minimum_dated_entry.mood, "vaguely ok")
        self.assertTrue(bare_minimum_dated_entry.uid, "1:49 AM")
        self.assertIsNone(bare_minimum_dated_entry.title)
        self.assertIsNone(bare_minimum_dated_entry.note)
        self.assertTrue(bare_minimum_dated_entry.activities, [])

    def test_insufficient_dated_entries(self):
        self.assertRaises(ValueError, DatedEntry, "2:00", mood="", known_moods={"neutral": ["vaguely ok"]})
