from unittest import TestCase

import librarian
from librarian import Librarian


class TestLibrarian(TestCase):
    """
    Tests the Librarian handler-class of the journal.
    The Librarian is responsible for parsing files and outputting the final journal.
    We use internal class methods to check proper handling of data throughout the process.
    """
    def test_init_valid_csv(self):
        self.assertTrue(Librarian("_tests/sheet-1-valid-data.csv"))

    def test_init_invalid_csv(self):
        """
        Pass faulty files and see if it fails as expected.
        """
        self.assertRaises(librarian.CannotAccessFileError, Librarian, "_tests/sheet-2-corrupted-bytes.csv")
        self.assertRaises(librarian.CannotAccessFileError, Librarian, "_tests/sheet-3-wrong-format.txt")
        self.assertRaises(librarian.CannotAccessFileError, Librarian, "_tests/sheet-4-no-extension")
        self.assertRaises(librarian.CannotAccessFileError, Librarian, "_tests/sheet-5-missing-file.csv")

        # TODO: handle this case in Librarian
        # self.assertRaises(librarian.CannotAccessFileError, Librarian, "_tests/sheet-6-empty-file.csv")

        # TODO: maybe generate corrupted_sheet and wrong_format during runner setup in workflow mode?
        # dd if=/dev/urandom of="$corrupted_file" bs=1024 count=10
        # generates random bytes and writes them into a given file

        # TODO: make this file locked during runner workflow with chmod 600
        self.assertRaises(librarian.CannotAccessFileError, Librarian, "locked-dir/locked_file.csv")

    def test_valid_access_dates(self):
        """
        All the following dates exist in the _tests/sheet-1-valid-data.csv and should be accessible by ``lib``.
        """
        # When
        lib = Librarian(
            path_to_file="_tests/sheet-1-valid-data.csv",
            path_to_moods="moods.json"
        )

        # Then
        self.assertTrue(lib.access_date("2022-10-25"))
        self.assertTrue(lib.access_date("2022-10-26"))
        self.assertTrue(lib.access_date("2022-10-27"))
        self.assertTrue(lib.access_date("2022-10-30"))

        # Check if get-item method of accessing date groups also works
        self.assertTrue(lib["2022-10-25"])
        self.assertTrue(lib["2022-10-26"])
        self.assertTrue(lib["2022-10-27"])
        self.assertTrue(lib["2022-10-30"])

    def test_wrong_access_dates(self):
        """
        **None** of the following dates exist in the _tests/sheet-1-valid-data.csv and should **NOT** be accessible by ``lib``.
        """
        # When
        lib = Librarian(
            path_to_file="_tests/sheet-1-valid-data.csv",
            path_to_moods="moods.json"
        )

        # Then can access valid dates, even if they weren't in the file
        self.assertTrue(lib.access_date("2022-10-21"))
        self.assertTrue(lib.access_date("2022-10-20"))
        self.assertTrue(lib.access_date("2022-10-2"))
        self.assertTrue(lib.access_date("1999-10-22"))
        # this dict method should also work
        self.assertTrue(lib["2005-01-19"])

        # But once I try to access the actual entries attached to those dates, they should be empty
        self.assertFalse(lib.access_date("2022-10-21").known_entries_from_this_day)
        self.assertFalse(lib.access_date("2022-10-20").known_entries_from_this_day)
        self.assertFalse(lib.access_date("2022-10-2").known_entries_from_this_day)
        self.assertFalse(lib.access_date("2022-10-22").known_entries_from_this_day)
        self.assertFalse(lib.access_date("1999-1-1").known_entries_from_this_day)

        # check if Librarian correctly raises ValueError when trying to check invalid dates
        self.assertRaises(ValueError, lib.access_date, "ABC")
        self.assertRaises(ValueError, lib.access_date, "2022")
        self.assertRaises(ValueError, lib.access_date, "12:00 AM")
        self.assertRaises(ValueError, lib.access_date, "1795-12-05")  # year range suspicious

    # CUSTOM AND STANDARD MOOD SETS
    # -----------------------------
    def test_custom_moods_when_passed_correctly(self):
        """Pass a valid JSON file and see if it knows it has access to custom moods now."""
        self.assertTrue(Librarian(
            path_to_file="_tests/sheet-1-valid-data.csv",
            path_to_moods="moods.json"
        ).current_mood_set.has_custom_moods)

    def test_custom_moods_when_not_passed(self):
        """Pass no moods and see if it know it only has standard moods available."""
        self.assertFalse(Librarian(
            path_to_file="_tests/sheet-1-valid-data.csv"
        ).current_mood_set.has_custom_moods)

    def test_custom_moods_with_invalid_jsons(self):
        """Pass faulty moods and see if it fails as expected."""
        self.assertRaises(
            librarian.CannotAccessCustomMoodsError,
            Librarian, "_tests/_tests/sheet-1-valid-data.csv", "_tests/output-results", "empty_sheet.csv"
        )

    def test_custom_moods_when_json_invalid(self):
        self.assertRaises(librarian.CannotAccessCustomMoodsError,
                          Librarian, "_tests/_tests/sheet-1-valid-data.csv", "_tests/output-results/", "empty_sheet.csv")
        self.assertRaises(librarian.CannotAccessCustomMoodsError,
                          Librarian, "_tests/_tests/sheet-1-valid-data.csv", "_tests/output-results/", "missing-file.json")
        self.assertRaises(librarian.CannotAccessCustomMoodsError,
                          Librarian, "_tests/_tests/sheet-1-valid-data.csv", "_tests/output-results/", "locked-dir/locked_file.csv")

    def test_custom_moods_that_are_incomplete(self):
        """
        Moodverse can deal with incomplete moods because the file merely expands its default knowledge.
        However, it can only expand it (and be truthy) if the dict with moods has all required groups.
        Therefore, since ``incomplete-moods`` lacks the ``good`` group, the assertion will evaluate to False.
        """
        lib_to_test = Librarian("_tests/sheet-1-valid-data.csv", "_tests/output-results/", "_tests/incomplete-moods.json")
        self.assertFalse(lib_to_test.current_mood_set.has_custom_moods)
