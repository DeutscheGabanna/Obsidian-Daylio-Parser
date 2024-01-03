import csv
import json
from unittest import TestCase
from librarian import Librarian


class TestLibrarian(TestCase):
    """
    Tests the Librarian handler-class of the journal.
    The Librarian is responsible for parsing files and outputting the final journal.
    We use internal class methods to check proper handling of data throughout the process.
    """
    def test_set_custom_moods(self):
        """
        Pass faulty moods and see if Librarian notices it does not know any custom moods while parsing.
        """
        # assertTrue is not needed, because it would have already failed at setUp()
        self.assertFalse(Librarian("sheet-2-corrupted-bytes.csv").has_custom_moods())
        self.assertFalse(Librarian("sheet-3-wrong-format.txt").has_custom_moods())
        self.assertFalse(Librarian("sheet-4-no-extension.csv").has_custom_moods())
        self.assertFalse(Librarian("incomplete-moods.json").has_custom_moods())

    def test_pass_file(self):
        """
        Pass some faulty files at the librarian and see if it exists.
        There is no point in continuing the script if a crucial CSV file is faulty.
        """
        # TODO: maybe generate corrupted_sheet and wrong_format during runner setup in workflow mode?
        # dd if=/dev/urandom of="$corrupted_file" bs=1024 count=10
        # generates random bytes and writes them into a given file
        self.assertRaises(csv.Error, Librarian, "sheet-2-corrupted-bytes.csv")
        self.assertRaises(csv.Error, Librarian, "sheet-3-wrong-format.txt")
        self.assertRaises(csv.Error, Librarian, "sheet-4-no-extension")
        self.assertRaises(FileNotFoundError, Librarian, "sheet-5-missing-file.csv")
        self.assertRaises(StopIteration, Librarian, "sheet-6-empty-file.csv")
        # TODO: make this file locked during runner workflow with chmod 600
        self.assertRaises(PermissionError, Librarian, "locked-dir/locked_file.csv")

    def test_access_date(self):
        """
        accessDate() should:
        - return True if lib contains Date obj, and return obj
        - return False if lib does not contain Date obj, and return empty obj
        - throw ValueError if the string does not follow day format
        """
        lib = Librarian(
            path_to_file="sheet-1-valid-data.csv",
            path_to_moods="../moods.json"
        )
        # obj is truthy if it has uid and at least one child DatedEntry (debatable)
        self.assertTrue(lib.access_date("2022-10-25"))
        self.assertTrue(lib.access_date("2022-10-26"))
        self.assertTrue(lib.access_date("2022-10-27"))
        self.assertTrue(lib.access_date("2022-10-30"))

        # obj is falsy if the object has no child DatedEntry (debatable)
        self.assertRaises(FileNotFoundError, lib.access_date, "2022-10-21")
        self.assertRaises(FileNotFoundError, lib.access_date, "2022-10-20")
        self.assertRaises(FileNotFoundError, lib.access_date, "2017-10-20")
        self.assertRaises(FileNotFoundError, lib.access_date, "1819-10-20")

        self.assertRaises(ValueError, lib.access_date, "ABC")
        self.assertRaises(ValueError, lib.access_date, "2022")
        self.assertRaises(ValueError, lib.access_date, "1999-1-1")
        self.assertRaises(ValueError, lib.access_date, "12:00 AM")

    def test_has_custom_moods(self):
        self.assertTrue(Librarian(
            path_to_file="sheet-1-valid-data.csv",
            path_to_moods="../moods.json"
        ).has_custom_moods())
        self.assertFalse(Librarian("sheet-1-valid-data.csv"))
        self.assertRaises(json.JSONDecodeError, Librarian, "sheet-1-valid-data.csv", "empty_sheet.csv")
        self.assertRaises(FileNotFoundError, Librarian, "sheet-1-valid-data.csv", "missing-file.json")
        self.assertRaises(PermissionError, Librarian, "sheet-1-valid-data.csv", "locked-dir/locked_file.csv")
        self.assertRaises(KeyError, Librarian, "sheet-1-valid-data.csv", "incomplete-moods.json")
