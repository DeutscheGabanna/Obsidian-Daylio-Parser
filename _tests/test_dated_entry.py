from unittest import TestCase
import hack
import dated_entry


class Test(TestCase):
    def test_slice_quotes(self):
        self.assertEqual(dated_entry.slice_quotes("\"test\""), "test")
        self.assertEqual(dated_entry.slice_quotes("\"\""), "")

    def test_is_time_valid(self):
        # Valid time formats
        self.assertTrue(dated_entry.Time("1:49 AM"))
        self.assertTrue(dated_entry.Time("02:15 AM"))
        self.assertTrue(dated_entry.Time("12:00 PM"))
        self.assertTrue(dated_entry.Time("6:30 PM"))
        self.assertTrue(dated_entry.Time("9:45 PM"))
        self.assertTrue(dated_entry.Time("00:00 AM"))
        self.assertTrue(dated_entry.Time("12:00 AM"))
        self.assertTrue(dated_entry.Time("13:30"))
        self.assertTrue(dated_entry.Time("9:45"))

        # Invalid time formats
        self.assertRaises(ValueError, dated_entry.Time, "okk:oksdf s")
        self.assertRaises(ValueError, dated_entry.Time, "14:59 AM")
        self.assertRaises(ValueError, dated_entry.Time, "25:00 AM")
        self.assertRaises(ValueError, dated_entry.Time, "26:10")
        self.assertRaises(ValueError, dated_entry.Time, "12:60 PM")
        self.assertRaises(ValueError, dated_entry.Time, "12:00 XX")
        self.assertRaises(ValueError, dated_entry.Time, "abc:def AM")
        self.assertRaises(ValueError, dated_entry.Time, "24:00 PM")
        self.assertRaises(ValueError, dated_entry.Time, "00:61 AM")
