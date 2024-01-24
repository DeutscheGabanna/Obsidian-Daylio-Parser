from unittest import TestCase

from src.dated_entry import \
    Time, \
    slice_quotes, \
    DatedEntry, \
    IsNotTimeError, \
    is_time_format_valid, \
    is_time_range_valid


# TODO: more test coverage needed

class TestDatedEntryUtils(TestCase):
    def test_is_time_format_valid(self):
        self.assertTrue(is_time_format_valid("1:49 AM"))
        self.assertTrue(is_time_format_valid("02:15"))
        self.assertTrue(is_time_format_valid("12:00"))
        self.assertTrue(is_time_format_valid("1:49 PM"))
        self.assertFalse(is_time_format_valid("1::49"))
        self.assertFalse(is_time_format_valid("12:60 AM"))
        # noinspection SpellCheckingInspection
        self.assertFalse(is_time_format_valid("okk:oksdf s"))
        self.assertFalse(is_time_format_valid("25:00 AM"))
        self.assertFalse(is_time_format_valid("26:10"))
        self.assertFalse(is_time_format_valid("12:60 PM"))
        self.assertFalse(is_time_format_valid("12:00 XX"))
        self.assertFalse(is_time_format_valid("abc:def AM"))
        self.assertFalse(is_time_format_valid("abc:def XM"))
        self.assertFalse(is_time_format_valid("24:00 PM"))
        self.assertFalse(is_time_format_valid("00:61 AM"))
        self.assertFalse(is_time_format_valid("---"))
        self.assertFalse(is_time_format_valid("23y7vg"))
        self.assertFalse(is_time_format_valid("::::"))
        self.assertFalse(is_time_format_valid("????"))
        self.assertFalse(is_time_format_valid("00000:000000000000"))
        self.assertFalse(is_time_format_valid("99:12"))
        self.assertFalse(is_time_format_valid("11:12 UU"))
        self.assertFalse(is_time_format_valid("9::12"))

        # as expected, this will return True, because we're not checking ranges yet
        self.assertTrue(is_time_format_valid("14:59 AM"))

    def test_is_time_range_valid(self):
        self.assertTrue(is_time_range_valid("11:00 AM"))
        self.assertTrue(is_time_range_valid("3:00 AM"))
        self.assertTrue(is_time_range_valid("7:59 AM"))
        self.assertTrue(is_time_range_valid("17:50"))
        self.assertTrue(is_time_range_valid("21:37"))
        self.assertTrue(is_time_range_valid("00:00"))
        self.assertTrue(is_time_range_valid("14:25"))

        self.assertFalse(is_time_range_valid("31:00"))
        self.assertFalse(is_time_range_valid("11:79"))
        self.assertFalse(is_time_range_valid("20:99 PM"))
        self.assertFalse(is_time_range_valid("-5:12"))
        self.assertFalse(is_time_range_valid("-5:-12"))
        self.assertFalse(is_time_range_valid("-5:-12"))
        self.assertFalse(is_time_range_valid("13:00 AM"))
        self.assertFalse(is_time_range_valid("15:00 PM"))

    def test_slice_quotes(self):
        self.assertEqual("test", slice_quotes("\"test\""))
        self.assertEqual("", slice_quotes("\"\""))
        self.assertEqual("bicycle", slice_quotes("\" bicycle   \""))


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

    def test_str(self):
        self.assertEqual("1:49 AM", str(Time("1:49 AM")))
        self.assertEqual("02:15 AM", str(Time("02:15 AM")))
        self.assertEqual("12:00 PM", str(Time("12:00 PM")))
        self.assertEqual("6:30 PM", str(Time("6:30 PM")))
        self.assertEqual("9:45 PM", str(Time("9:45 PM")))
        self.assertEqual("00:00 AM", str(Time("00:00 AM")))
        self.assertEqual("12:00 AM", str(Time("12:00 AM")))
        self.assertEqual("13:30", str(Time("13:30")))
        self.assertEqual("9:45", str(Time("9:45")))


class TestDatedEntry(TestCase):
    def test_bare_minimum_dated_entries(self):
        # When
        bare_minimum_dated_entry = DatedEntry(
            time="1:49 AM",
            mood="vaguely ok"
        )

        # Then
        self.assertEqual("vaguely ok", bare_minimum_dated_entry.mood)
        self.assertEqual("1:49 AM", bare_minimum_dated_entry.uid)
        self.assertIsNone(bare_minimum_dated_entry.title)
        self.assertIsNone(bare_minimum_dated_entry.note)
        self.assertListEqual([], bare_minimum_dated_entry.activities)

    def test_insufficient_dated_entries(self):
        self.assertRaises(ValueError, DatedEntry, time="2:00", mood="")
