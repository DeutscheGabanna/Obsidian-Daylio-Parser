from unittest import TestCase
from dated_entries_group import DatedEntriesGroup


class TestDate(TestCase):
    def setUp(self):
        self.sample_date = DatedEntriesGroup("2011-10-10")

    def test_get_date(self):
        self.assertEqual(DatedEntriesGroup("2023-10-15").get_uid(), "2023-10-15")
        self.assertEqual(DatedEntriesGroup("2019-5-9").get_uid(), "2019-5-9")
        self.assertEqual(DatedEntriesGroup("2023-11-25").get_uid(), "2023-11-25")

        self.assertRaises(ValueError, DatedEntriesGroup, "00-")
        self.assertRaises(ValueError, DatedEntriesGroup, "2199-32-32")

        # Test cases with unconventional date formats
        self.assertRaises(ValueError, DatedEntriesGroup, "2022/05/18")  # Invalid separator
        self.assertRaises(ValueError, DatedEntriesGroup, "2023_07_12")  # Invalid separator
        self.assertRaises(ValueError, DatedEntriesGroup, "1999.10.25")  # Invalid separator

        # Test cases with random characters in the date string
        self.assertRaises(ValueError, DatedEntriesGroup, "2@#0$2-05-18")  # Special characters in the year
        self.assertRaises(ValueError, DatedEntriesGroup, "1987-0%4-12")  # Special characters in the month
        self.assertRaises(ValueError, DatedEntriesGroup, "2001-07-3*")  # Special characters in the day

        # Test cases with excessive spaces
        self.assertRaises(ValueError, DatedEntriesGroup, "   2022-05-18  ")  # Spaces around the date
        self.assertRaises(ValueError, DatedEntriesGroup, "1999- 10-25")  # Space after the month
        self.assertRaises(ValueError, DatedEntriesGroup, "  2000-04 -  12  ")  # Spaces within the date

        # Test cases with mixed characters and numbers
        self.assertRaises(ValueError, DatedEntriesGroup, "2k20-05-18")  # Non-numeric characters in the year
        self.assertRaises(ValueError, DatedEntriesGroup, "1999-0ne-25")  # Non-numeric characters in the month
        self.assertRaises(ValueError, DatedEntriesGroup, "2021-07-Two")  # Non-numeric characters in the day

        # Test cases with missing parts of the date
        self.assertRaises(ValueError, DatedEntriesGroup, "2022-05")  # Missing day
        self.assertRaises(ValueError, DatedEntriesGroup, "1987-09")  # Missing day
        self.assertRaises(ValueError, DatedEntriesGroup, "2001")  # Missing month and day
        self.assertRaises(ValueError, DatedEntriesGroup, "")  # Empty string

    def test_access_dated_entry(self):
        """
        Difference between access_dated_entry(time) and get_known_dated_entries[time]:
        - former will create missing entries, if time is valid
        - latter will raise KeyError if the entry is missing, even if time is valid
        - former will raise ValueError if time is invalid
        - latter will raise KeyError if time is invalid
        """
        self.assertEqual(self.sample_date.access_dated_entry("10:00 AM").get_uid(), "10:00 AM")
        self.assertEqual(self.sample_date.access_dated_entry("9:30 PM").get_uid(), "9:30 PM")

        # Test cases for 12-hour format
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "2: AM")  # Invalid format
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "15:45 PM")  # Invalid hour (more than 12)
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "11:30 XM")  # Invalid meridiem indicator

        # Test cases for 24-hour format
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "25:15")  # Invalid hour (more than 24)
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "14:45 PM")
        self.assertRaises(ValueError, self.sample_date.access_dated_entry,
                          "03:20 XM")  # Invalid meridiem indicator in 24-hour format

        # Test cases with invalid characters
        # noinspection SpellCheckingInspection
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "/ASDFVDJU\\")  # Invalid characters

        # Test cases with incomplete time information
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "2022-1")  # Incomplete time information
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, "12:")  # Incomplete time information
        self.assertRaises(ValueError, self.sample_date.access_dated_entry, ":30")  # Incomplete time information

    def test_get_known_dated_entries(self):
        """
        Difference between access_dated_entry(time) and get_known_dated_entries[time]:
        - former will create missing entries, if time is valid
        - latter will raise KeyError if the entry is missing, even if time is valid
        - former will raise ValueError if time is invalid
        - latter will raise KeyError if time is invalid
        """
        self.sample_date.access_dated_entry("11:11")
        self.sample_date.access_dated_entry("12:12")
        self.sample_date.access_dated_entry("13:13")

        self.assertEqual(self.sample_date.get_known_dated_entries()["11:11"].get_uid(), "11:11")
        self.assertEqual(self.sample_date.get_known_dated_entries()["12:12"].get_uid(), "12:12")
        self.assertEqual(self.sample_date.get_known_dated_entries()["13:13"].get_uid(), "13:13")

        self.assertRaises(KeyError, lambda: self.sample_date.get_known_dated_entries()["23:00"])
        self.assertRaises(KeyError, lambda: self.sample_date.get_known_dated_entries()["9:30 PM"])
        self.assertRaises(KeyError, lambda: self.sample_date.get_known_dated_entries()["11:50 AM"])

    def test_truthiness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be truthy if it has a valid UID and has any known entries.
        """
        self.sample_date.access_dated_entry("11:11")
        self.sample_date.access_dated_entry("12:12")
        self.sample_date.access_dated_entry("13:13")

        self.assertTrue(self.sample_date)

    def test_falseness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be falsy if it has a valid UID but no known entries.
        """
        self.assertFalse(self.sample_date)

    def test_no_duplicate_entries_created(self):
        """
        DatedEntriesGroup should return the already existing entry if it is known, instead of creating a duplicate.
        """
        obj = self.sample_date.access_dated_entry("11:11")
        obj.set_note("I already exist, see?")

        self.assertEqual(self.sample_date.access_dated_entry("11:11").get_note(), obj.get_note())

    def test_retrieve_known_entries(self):
        obj1 = self.sample_date.access_dated_entry("11:11")
        obj2 = self.sample_date.access_dated_entry("12:12")
        obj3 = self.sample_date.access_dated_entry("13:13")

        self.assertEqual(self.sample_date.get_known_dated_entries()["11:11"], obj1)
        self.assertEqual(self.sample_date.get_known_dated_entries()["12:12"], obj2)
        self.assertEqual(self.sample_date.get_known_dated_entries()["13:13"], obj3)