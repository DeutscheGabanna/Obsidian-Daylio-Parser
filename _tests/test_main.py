"""Unit tests for Daylio-Obsidian parser"""
import unittest
from handlers import Librarian
from handlers import DayNotInJournalError
from handlers import InvalidDateFormatError
from handlers import EntryNotInJournalError

class TestLibrarian(unittest.TestCase):
    """
    Tests the Librarian handler-class of the journal.
    The Librarian is responsible for parsing files and outputing the final journal.
    We use internal class methods to check proper handling of data throughout the process. 
    """
    def setUp(self):
        self.lib = Librarian().passMoods("moods.json").passFile("_tests/testing_sheet.csv")
    
    def test_no_moods(self):
        """
        When passed a file to parse, Librarian obj should inform about:
        - no moods.json file if it hasn't been provided
        TODO: Librarian should pass a test if passMoods() was called before passFile()
        """
        with self.assertLogs('runtime', level="INFO"):
            Librarian().passFile("_tests/testing_sheet.csv")

    def test_bad_files(self):
        """Pass some faulty files at the librarian and see if it throws correct erorrs"""
        # TODO: maybe generate corrupted_sheet and wrong_format during runner setup in workflow mode?
        # dd if=/dev/urandom of="$corrupted_file" bs=1024 count=10
        # generates random bytes and writes them into a given file
        self.assertRaises(ValueError, Librarian().passFile("_tests/corrupted_sheet.csv"))
        self.assertRaises(TypeError, Librarian().passFile("_tests/wrong_format.txt"))
        self.assertRaises(TypeError, Librarian().passFile("_tests/wrong_format_no_ext"))
        self.assertRaises(FileNotFoundError, Librarian().passFile("_tests/missing_file.csv"))
        # TODO: make this file locked during runner workflow with chmod 600
        self.assertRaises(PermissionError, Librarian().passFile("_tests/locked-dir/locked_file.csv"))

    def access(self, date, dated_entry = None):
        """ Alias to detach actual object names and their methods from repetitive test calls"""
        if dated_entry is None:
            obj = self.lib.accessDate(date)
        else:
            obj = self.lib.accessDate(date).accessDatedEntry(dated_entry)
        return obj

    def test_is_day_filed(self):
        """
        accessDate() should:
        - return True if lib contains Date obj, and return obj
        - return False if lib does not contain Date obj, and return empty obj
        - throw ValueError if the string does not follow day format
        """
        self.assertTrue(self.access("2022-10-25"))
        self.assertTrue(self.access("2022-10-26"))
        self.assertTrue(self.access("2022-10-27"))
        self.assertTrue(self.access("2022-10-30"))

        # TODO: __bool__ method should be falsy if the object has no child DatedEntry
        self.assertFalse(self.access("2022-10-21"))
        self.assertFalse(self.access("2022-10-20"))
        self.assertFalse(self.access("2017-10-20"))
        self.assertFalse(self.access("1819-10-20"))

        self.assertRaises(ValueError, self.lib.access("ABC"))
        self.assertRaises(ValueError, self.lib.access("2022"))
        self.assertRaises(ValueError, self.lib.access("1999-1-1"))
        self.assertRaises(ValueError, self.lib.access("12:00 AM"))

    def test_is_entry_filed(self):
        """
        accessDate().accessDatedEntry() should:
        - return True if lib contains DatedEntry obj, and return obj
        - return False if lib does not contain DatedEntry obj, and return empty obj
        - throw ValueError if the strings do not follow day & time format
        """
        d = "2022-10-25"
        self.assertTrue(self.lib.access(d, "11:36 PM"))
        self.assertTrue(self.lib.access(d, "11:40 PM"))
        self.assertTrue(self.lib.access(d, "5:00 PM"))
        self.assertFalse(self.lib.access(d, "12:00 AM"))

        d = "2022-10-26"
        self.assertTrue(self.lib.access(d, "10:00 PM"))
        self.assertTrue(self.lib.access(d, "8:00 PM"))
        self.assertTrue(self.lib.access(d, "7:30 PM"))
        self.assertTrue(self.lib.access(d, "1:00 PM"))
        self.assertTrue(self.lib.access(d, "9:00 AM"))
        self.assertTrue(self.lib.access(d, "7:50 AM"))
        self.assertFalse(self.lib.access(d, "2:05 PM"))

        d = "2022-10-27"
        self.assertTrue(self.lib.access(d, "1:49 PM"))
        self.assertTrue(self.lib.access(d, "12:00 AM"))
        self.assertFalse(self.lib.access(d, "2:59 AM"))

        d = "2022-10-30"
        self.assertTrue(self.lib.access(d, "10:04 AM"))
        self.assertFalse(self.lib.access(d, "11:09 AM"))

        self.assertRaises(ValueError, self.lib.access("2022-1", "12:00 AM")) # wrong day format
        self.assertRaises(ValueError, self.lib.access("2022-1", "2: AM")) # both formats wrong
        self.assertRaises(ValueError, self.lib.access("WHAT", "IS GOING ON"))
        self.assertRaises(ValueError, self.lib.access("/ASDFVDJU\\", "%#"))

    def test_getters(self):
        """
        getX() retrieves a given property of the Date/DatedEntry object. It should:
        - be equal to the expected value if we query an existing DatedEntry
        - throw DatedEntryNotFoundError if we query an empty DatedEntry obj
        """
        d = "2022-10-25"
        note = "Nulla vel risus eget magna lacinia aliquam ac in arcu."
        self.assertEqual(self.access(d, "11:36 PM").getMood(), "hungry")
        self.assertEqual(self.access(d, "11:36 PM").getNote(), note)
        self.assertNotEqual(self.access(d, "5:00 PM").getMood(), "rad")

        d = "2022-10-26"
        note = "QYuip."
        self.assertEqual(self.access(d, "10:00 PM").getMood(), "captivated")
        self.assertNotEqual(self.access(d, "8:00 PM").getNote(), note)
        self.assertNotEqual(self.access(d, "7:30 PM").getMood(), "blissful")

        d = "2022-10-27"
        activities = [ "allegro", "working-remotely" ]
        self.assertEqual(self.access(d, "12:00 AM").getMood(), "fatigued")
        self.assertListEqual(self.access(d, "12:00 AM").getActivites(), activities)
        self.assertNotEqual(self.access(d, "1:49 PM").getMood(), "guilty")
        self.assertNotEqual(self.access(d, "1:49 PM").getActivites(), activities)

        d = "2022-10-30"
        self.assertEqual(self.lib.accessDate(d, "10:04 AM").getMood(), "vaguely ok")
        self.assertNotEqual(self.lib.accessDate(d, "10:04 AM").getMood(), "captivated")

        self.assertRaises(DatedEntryNotFoundError, self.access("2022-10-25", "1:13 PM").getMood(), "rad")
        self.assertRaises(DatedEntryNotFoundError, self.access("1999-05-26", "11:15 M").getMood(), "blissful")
        self.assertRaises(DatedEntryNotFoundError, self.access("2022-10-27", "3:51 PM").getMood(), "guilty")
        self.assertRaises(ValueError, self.access("2022-10-26", "29:04 AM").getMood(), "captivated")

        # Try to query a property of DatedEntry (e.g. mood) in a Date object
        self.assertRaises(AttributeError, self.access(d).getMood())
        self.assertRaises(AttributeError, self.access(d).getActivites())

        # Reverse - try to query a property of Date in a DatedEntry object
        self.assertRaises(AttributeError, self.access(d, "10:04 AM").getBoilerplate())

    def testOutputBoilerplate(self):
        """
        outputBoilerplate() is normally a private method, but we want to check if:
        - it throws an error when trying to output without destination set
        - it throws an error when invoked from a missing Date
        - it throws an error when invoked in DatedEntry obj instead of Date obj
        - it returns True when succeeds 
        """
        d = "2022-10-26"
        # at this point the destination dir has not been set in Librarian obj
        self.assertRaises(UnknownDestinationError, self.access(d).outputBoilerplate())
        # now we correctly set it to output to pwd
        self.assertTrue(self.lib.setOutput("_tests/").outputBoilerplate())
        self.assertRaises(DatedEntryNotFoundError, self.access("1999-09-25").outputBoilerplate())
        self.assertRaises(DatedEntryNotFoundError, self.access(d, "7:30 AM").outputBoilerplate())

    def testOutputPartial(self):
        """
        output() for DatedEntry obj should output its contents into lib destination
        Actual comparison between outputted and expected text at github-workflow stage
        """
        d = "2022-10-26"
        self.assertTrue(self.lib.accessDate(d).accessDatedEntry("7:30 PM").output())
        self.assertTrue(self.lib.accessDate(d).accessDatedEntry("8:00 PM").output())

    def testOutputFullDate(self):
        """
        output() for Date obj should output boilerplate & all its DatedEntry children
        Actual comparison between outputted and expected text at github-workflow stage
        """
        d = "2022-10-26"
        self.assertTrue(self.lib.accessDate(d).output())

    def testOutputAll(self):
        """
        output() for Librarian obj should output all Date children
        Actual comparison between outputted and expected text at github-workflow stage
        """
        self.assertTrue(self.lib.output("_tests/output/"))
        self.assertRaises(NotADirectoryError, self.lib.setOutput("_tests/dev-null").output())
        self.assertRaises(FileNotFoundError, self.lib.setOutput("_tests/it/does/not/exist").output())
        self.assertRaises(PermissionError, self.lib.setOutput("_tests/locked-dir").output())

# is this run as a main program, not component?
if __name__ == '__main__':
    unittest.main(argv=["first-arg-is-ignored"])
