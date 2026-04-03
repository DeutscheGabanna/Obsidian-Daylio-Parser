from unittest import TestCase

from daylio_to_md.entry.mood import Moodverse
from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.librarian import Librarian, CannotAccessJournalError
from daylio_to_md.group import EntriesFromBuilder
from daylio_to_md.reader import CsvJournalReader


class TestLibrarian(TestCase):
    """
    Tests the Librarian handler-class of the journal.
    The Librarian is responsible for parsing rows from a reader and assembling a Journal.
    We use the new reader → parse() → Journal pipeline.
    """

    def test_parse_valid_csv(self):
        reader = CsvJournalReader("tests/files/all-valid.csv")
        journal = Librarian(reader).parse()
        self.assertTrue(journal)

    def test_parse_invalid_csv(self):
        """
        Pass faulty files and see if it fails as expected.
        """
        self.assertRaises(
            CannotAccessJournalError,
            Librarian(CsvJournalReader("tests/files/scenarios/fail/corrupted.csv")).parse
        )
        self.assertRaises(
            CannotAccessJournalError,
            Librarian(CsvJournalReader("tests/files/scenarios/fail/wrong-format.txt")).parse
        )
        # TODO: what to do with no extension file?
        self.assertRaises(
            CannotAccessJournalError,
            Librarian(CsvJournalReader("tests/files/fail/missing.csv")).parse
        )

        # TODO: handle this case in Librarian
        # self.assertRaises(EmptyJournalError,
        #     Librarian(CsvJournalReader("tests/files/scenarios/fail/empty.csv")).parse)

        # TODO: maybe generate corrupted_sheet and wrong_format during runner setup in workflow mode?
        # TODO: move check locked file test into Docker run

    def test_valid_access_dates(self):
        """
        All the following dates exist in the ``tests/files/all-valid.csv``.
        They should be accessible via the Journal.
        """
        reader = CsvJournalReader("tests/files/all-valid.csv")
        mood_set = Moodverse.from_file("all-valid.json")
        journal = Librarian(reader, mood_set).parse()

        self.assertTrue(journal["2022-10-25"])
        self.assertTrue(journal["2022-10-26"])
        self.assertTrue(journal["2022-10-27"])
        self.assertTrue(journal["2022-10-30"])

    def test_wrong_access_dates(self):
        """
        **None** of the following dates exist in the ``tests/files/all-valid.csv``.
        Therefore, they should **NOT** be accessible via the Journal.
        """
        reader = CsvJournalReader("tests/files/all-valid.csv")
        mood_set = Moodverse.from_file("all-valid.json")
        journal = Librarian(reader, mood_set).parse()

        self.assertRaises(KeyError, lambda: journal["2022-10-21"])
        self.assertRaises(KeyError, lambda: journal["2022-10-20"])
        self.assertRaises(KeyError, lambda: journal["2022-10-2"])
        self.assertRaises(KeyError, lambda: journal["1999-10-22"])

        # check if Journal correctly raises ValueError when trying to check invalid dates
        self.assertRaises(ValueError, lambda: journal["ABC"])
        self.assertRaises(ValueError, lambda: journal["2022"])
        self.assertRaises(ValueError, lambda: journal["12:00 AM"])

    # CUSTOM AND STANDARD MOOD SETS
    # -----------------------------
    def test_custom_moods_when_passed_correctly(self):
        """Pass a valid JSON file and see if it knows it has access to custom moods now."""
        reader = CsvJournalReader("tests/files/all-valid.csv")
        mood_set = Moodverse.from_file("tests/files/all-valid.json")
        journal = Librarian(reader, mood_set).parse()
        self.assertTrue(journal.mood_set.get_custom_moods)

    def test_custom_moods_when_not_passed(self):
        """Pass no moods and see if it knows it only has standard moods available."""
        reader = CsvJournalReader("tests/files/all-valid.csv")
        journal = Librarian(reader).parse()
        self.assertEqual(0, len(journal.mood_set.get_custom_moods), msg=journal.mood_set)

    def test_custom_moods_with_invalid_jsons(self):
        """Pass faulty moods and see if it has no custom moods loaded."""
        reader = CsvJournalReader("tests/files/all-valid.csv")
        mood_set = Moodverse.from_file("tests/files/scenarios/fail/empty.csv")
        journal = Librarian(reader, mood_set).parse()
        self.assertEqual(0, len(journal.mood_set.get_custom_moods))

    def test_custom_moods_when_json_invalid(self):
        reader = CsvJournalReader("tests/files/all-valid.csv")

        mood_set = Moodverse.from_file("tests/files/scenarios/fail/empty.csv")
        journal = Librarian(reader, mood_set).parse()
        default = Moodverse()
        self.assertDictEqual(journal.mood_set.get_moods, default.get_moods,
                             msg="\n".join([
                                 "current ID:\t" + str(id(journal.mood_set)),
                                 "default object ID:\t" + str(id(default))
                             ])
                             )

        mood_set = Moodverse.from_file("tests/files/scenarios/fail/incomplete.csv")
        journal = Librarian(CsvJournalReader("tests/files/all-valid.csv"), mood_set).parse()
        self.assertDictEqual(journal.mood_set.get_moods, default.get_moods,
                             msg="\n".join([
                                 "current ID:\t" + str(id(journal.mood_set)),
                                 "default object ID:\t" + str(id(default))
                             ])
                             )
        # TODO: move locked folder and locked file tests into Docker run
        self.assertDictEqual(journal.mood_set.get_moods, default.get_moods,
                             msg="\n".join([
                                 "current ID:\t" + str(id(journal.mood_set)),
                                 "default object ID:\t" + str(id(default))
                             ])
                             )

    def test_custom_moods_that_are_incomplete(self):
        """
        Moodverse can deal with incomplete moods because the file merely expands its default knowledge.
        However, it can only expand it (and be truthy) if the dict with moods has all required groups.
        Therefore, since ``incomplete-moods`` lacks the ``good`` group, the assertion will evaluate to False.
        """
        custom_config = EntriesFromBuilder(entries_builder=EntryBuilder(tag_activities=True))
        reader = CsvJournalReader("tests/files/scenarios/ok/all-valid.csv")
        mood_set = Moodverse.from_file("tests/files/moods/incomplete.json")
        journal = Librarian(reader, mood_set, custom_config).parse()
        # There are 11 moods, out of which one is a duplicate of a default mood, so 10 custom in total
        self.assertEqual(10, len(journal.mood_set.get_custom_moods),
                         msg=journal.mood_set.get_custom_moods.keys())
