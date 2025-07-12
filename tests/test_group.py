import datetime
from unittest import TestCase

from daylio_to_md.group import \
    EntriesFrom, \
    EntryMissingError, \
    IncompleteDataRow
from daylio_to_md.utils import InvalidDateError, InvalidTimeError


class TestDate(TestCase):
    def setUp(self):
        # Create a sample date
        self.sample_date = EntriesFrom("2011-10-10")
        # Append two sample entries to that day
        self.sample_date.create_entry(
            {
                "time": "10:00 AM",
                "mood": "vaguely ok",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )
        self.sample_date.create_entry(
            {
                "time": "9:30 PM",
                "mood": "awful",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )

    def test_creating_duplicates_which_are_allowed_in_daylio(self):
        # TODO: actually test this
        self.sample_date.create_entry(
            {
                "time": "10:00 AM",
                "mood": "vaguely ok",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )

    def test_creating_entries_from_row(self):
        """
        Test whether you can successfully create :class:`Entry` objects from this builder class.
        """
        my_date = EntriesFrom("1999-05-07")
        my_date.create_entry(
            {
                "time": "10:00 AM",
                "mood": "vaguely ok",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )
        # This lacks the minimum required keys - time and mood - to function correctly
        with self.assertRaises(IncompleteDataRow):
            my_date.create_entry(
                {
                    "time": "5:00 PM",
                    "mood": "",
                    "activities": "",
                    "note_title": "",
                    "note": ""
                }
            )

    def test_create_entry_groups(self):
        """
        Try to instantiate an object of :class:`DatedEntriesGroup` with either valid or invalid dates
        """
        # str() function converts the object's uid, which in this case is a datetime.date object.
        self.assertEqual("2023-10-15", str(EntriesFrom("2023-10-15")))
        self.assertEqual("2019-05-09", str(EntriesFrom("2019-5-9")))
        self.assertEqual("2023-11-25", str(EntriesFrom("2023-11-25")))
        # direct comparison with a datetime.date object should on comparing only their dates
        self.assertEqual(
            datetime.date(2023, 10, 15),
            EntriesFrom("2023-10-15").date)
        self.assertEqual(
            datetime.date(2022, 5, 18),
            EntriesFrom("   2022-05-18  ").date)  # Spaces around the date

        self.assertRaises(InvalidDateError, EntriesFrom, "00-")
        self.assertRaises(InvalidDateError, EntriesFrom, "2199-32-32")

        # Test cases with unconventional date formats
        self.assertRaises(InvalidDateError, EntriesFrom, "2022/05/18")  # Invalid separator
        self.assertRaises(InvalidDateError, EntriesFrom, "2023_07_12")  # Invalid separator
        self.assertRaises(InvalidDateError, EntriesFrom, "1999.10.25")  # Invalid separator

        # Test cases with random characters in the date string
        self.assertRaises(InvalidDateError, EntriesFrom, "2@#0$2-05-18")  # Special characters in the year
        self.assertRaises(InvalidDateError, EntriesFrom, "1987-0%4-12")  # Special characters in the month
        self.assertRaises(InvalidDateError, EntriesFrom, "2001-07-3*")  # Special characters in the day

        # Test cases with excessive spaces
        self.assertRaises(InvalidDateError, EntriesFrom, "1999- 10-25")  # Spaces within the date
        self.assertRaises(InvalidDateError, EntriesFrom, "  2000-04 -  12  ")  # Spaces within the date

        # Test cases with mixed characters and numbers
        self.assertRaises(InvalidDateError, EntriesFrom, "2k20-05-18")  # Non-numeric characters in the year
        self.assertRaises(InvalidDateError, EntriesFrom, "1999-0ne-25")  # Non-numeric characters in the month
        self.assertRaises(InvalidDateError, EntriesFrom, "2021-07-Two")  # Non-numeric characters in the day

        # Test cases with missing parts of the date
        self.assertRaises(InvalidDateError, EntriesFrom, "2022-05")  # Missing day
        self.assertRaises(InvalidDateError, EntriesFrom, "1987-09")  # Missing day
        self.assertRaises(InvalidDateError, EntriesFrom, "2001")  # Missing month and day
        self.assertRaises(InvalidDateError, EntriesFrom, "")  # Empty string

    # noinspection PyStatementEffect,SpellCheckingInspection
    def test_access_dated_entry(self):
        self.assertEqual("21:30", str(self.sample_date["9:30PM"]))
        self.assertEqual(datetime.time(10, 0), self.sample_date["10:00"].time)

        # Test cases for 12-hour format
        with self.assertRaises(InvalidTimeError):
            self.sample_date["2: AM"]  # <- no minutes

        with self.assertRaises(InvalidTimeError):
            self.sample_date["15:45 PM"]  # <- above 12h

        with self.assertRaises(InvalidTimeError):
            self.sample_date["14:45 PM"]  # <- above 12h

        # noinspection SpellCheckingInspection
        with self.assertRaises(InvalidTimeError):
            self.sample_date["11:30 XM"]  # <- wrong meridiem

        # noinspection SpellCheckingInspection
        with self.assertRaises(InvalidTimeError):
            self.sample_date["03:20 XM"]  # <- wrong meridiem

        # Test cases for 24-hour format
        with self.assertRaises(InvalidTimeError):
            self.sample_date["25:15"]  # <- above 24h

        with self.assertRaises(InvalidTimeError):
            self.sample_date["11:78"]  # <- above 59m

        # Test cases with invalid characters
        with self.assertRaises(InvalidTimeError):
            self.sample_date["/ASDFVDJU\\"]

        # Other test cases with incomplete time information
        with self.assertRaises(InvalidTimeError):
            self.sample_date["2022-1"]

        with self.assertRaises(InvalidTimeError):
            self.sample_date["12:"]

        with self.assertRaises(InvalidTimeError):
            self.sample_date[":30"]

    def test_get_known_dated_entries(self):
        self.assertEqual("21:30", str(self.sample_date["9:30 PM"]))
        self.assertEqual("10:00", str(self.sample_date["10:00 AM"]))

        # Either Exception should work because the EntryMissingError is a subclass of KeyError
        self.assertRaises(KeyError, lambda: self.sample_date["23:00"])
        self.assertRaises(EntryMissingError, lambda: self.sample_date["11:50 AM"])

    def test_truthiness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be truthy if it has a valid UID and has any known entries.
        """
        self.assertGreater(len(self.sample_date.known_entries), 0)

    def test_falseness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be falsy if it has a valid UID but no known entries.
        """
        another_day = EntriesFrom("2019-09-12")
        self.assertEqual(len(another_day.known_entries), 0)
        self.assertFalse(another_day.known_entries)
