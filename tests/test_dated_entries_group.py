from unittest import TestCase, skip

import tests.suppress as suppress
from daylio_to_md.dated_entries_group import \
    DatedEntriesGroup, \
    InvalidDateError, \
    DatedEntryMissingError, \
    TriedCreatingDuplicateDatedEntryError, \
    IncompleteDataRow


class TestDate(TestCase):
    def setUp(self):
        # Create a sample date
        self.sample_date = DatedEntriesGroup("2011-10-10")
        # Append two sample entries to that day
        self.sample_date.create_dated_entry_from_row(
            {
                "time": "10:00 AM",
                "mood": "vaguely ok",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )
        self.sample_date.create_dated_entry_from_row(
            {
                "time": "9:30 PM",
                "mood": "awful",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )

    @suppress.out
    def test_creating_entries_from_row(self):
        """
        Test whether you can successfully create :class:`DatedEntry` objects from this builder class.
        """
        my_date = DatedEntriesGroup("1999-05-07")
        my_date.create_dated_entry_from_row(
            {
                "time": "10:00 AM",
                "mood": "vaguely ok",
                "activities": "",
                "note_title": "",
                "note": ""
            }
        )
        # This would be a duplicate from the one already created
        with self.assertRaises(TriedCreatingDuplicateDatedEntryError):
            my_date.create_dated_entry_from_row(
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
            my_date.create_dated_entry_from_row(
                {
                    "time": "5:00 PM",
                    "mood": "",
                    "activities": "",
                    "note_title": "",
                    "note": ""
                }
            )

    @suppress.out
    def test_create_dated_entries_groups(self):
        """
        Try to instantiate an object of :class:`DatedEntriesGroup` with either valid or invalid dates
        """
        self.assertEqual("2023-10-15", str(DatedEntriesGroup("2023-10-15")))
        self.assertEqual("2019-5-9", str(DatedEntriesGroup("2019-5-9")))
        self.assertEqual("2023-11-25", str(DatedEntriesGroup("2023-11-25")))

        self.assertRaises(InvalidDateError, DatedEntriesGroup, "00-")
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2199-32-32")

        # Test cases with unconventional date formats
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2022/05/18")  # Invalid separator
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2023_07_12")  # Invalid separator
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "1999.10.25")  # Invalid separator

        # Test cases with random characters in the date string
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2@#0$2-05-18")  # Special characters in the year
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "1987-0%4-12")  # Special characters in the month
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2001-07-3*")  # Special characters in the day

        # Test cases with excessive spaces
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "   2022-05-18  ")  # Spaces around the date
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "1999- 10-25")  # Space after the month
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "  2000-04 -  12  ")  # Spaces within the date

        # Test cases with mixed characters and numbers
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2k20-05-18")  # Non-numeric characters in the year
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "1999-0ne-25")  # Non-numeric characters in the month
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2021-07-Two")  # Non-numeric characters in the day

        # Test cases with missing parts of the date
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2022-05")  # Missing day
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "1987-09")  # Missing day
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "2001")  # Missing month and day
        self.assertRaises(InvalidDateError, DatedEntriesGroup, "")  # Empty string

    @suppress.out
    def test_access_dated_entry(self):
        """
        Uses the :class:`DatedEntryGroup` object from :func:`setUp` with sample entries.
        Tries to either access existing entries through :func:`access_dated_entry` or missing ones.
        Expected behaviour is for the :class:`DatedEntryGroup` to return the entry object if exists or raise exception.
        """
        self.assertEqual("10:00 AM", str(self.sample_date.access_dated_entry("10:00 AM")))
        self.assertEqual("9:30 PM", str(self.sample_date.access_dated_entry("9:30 PM")))

        # Test cases for 12-hour format
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "2: AM")  # <- no minutes
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "15:45 PM")  # <- above 12h
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "14:45 PM")  # <- above 12h
        # noinspection SpellCheckingInspection
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "11:30 XM")  # <- wrong meridiem
        # noinspection SpellCheckingInspection
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "03:20 XM")  # <- wrong meridiem

        # Test cases for 24-hour format
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "25:15")  # <- above 24h
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "11:78")  # <- above 59m

        # Test cases with invalid characters
        # noinspection SpellCheckingInspection
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "/ASDFVDJU\\")

        # Other test cases with incomplete time information
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "2022-1")
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, "12:")
        self.assertRaises(DatedEntryMissingError, self.sample_date.access_dated_entry, ":30")

    @suppress.out
    def test_get_known_dated_entries(self):
        """
        Difference between access_dated_entry(time) and get_known_dated_entries[time]:
        - former will create missing entries, if time is valid
        - latter will raise KeyError if the entry is missing, even if time is valid
        - former will raise ValueError if time is invalid
        - latter will raise KeyError if time is invalid
        """
        self.assertEqual("9:30 PM", str(self.sample_date.known_entries_from_this_day["9:30 PM"]))
        self.assertEqual("10:00 AM", str(self.sample_date.known_entries_from_this_day["10:00 AM"]))

        self.assertRaises(KeyError, lambda: self.sample_date.known_entries_from_this_day["23:00"])
        self.assertRaises(KeyError, lambda: self.sample_date.known_entries_from_this_day["11:50 AM"])

    @suppress.out
    def test_truthiness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be truthy if it has a valid UID and has any known entries.
        """
        self.assertGreater(len(self.sample_date.known_entries_from_this_day), 0)

    @suppress.out
    def test_falseness_of_dated_entries_group(self):
        """
        DatedEntriesGroup should be falsy if it has a valid UID but no known entries.
        """
        another_day = DatedEntriesGroup("2019-09-12")
        self.assertEqual(len(another_day.known_entries_from_this_day), 0)
        self.assertFalse(another_day.known_entries_from_this_day)

    @skip("not yet implemented")
    def test_no_duplicate_entries_created(self):
        """
        DatedEntriesGroup should return the already existing entry if it is known, instead of creating a duplicate.
        """
        self.assertEqual(True, True)

    @skip("not yet implemented")
    def test_retrieve_known_entries(self):
        self.assertEqual(True, True)
