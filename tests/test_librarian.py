from pathlib import Path

import pytest

from daylio_to_md.entry.mood import Moodverse
from daylio_to_md.group import EntriesFromBuilder
from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.librarian import Librarian, CannotAccessJournalError

TESTS_DIR = Path(__file__).resolve().parent
RESOURCES = TESTS_DIR / "resources"


class TestLibrarian:
    """
    Tests the Librarian handler-class of the journal.
    The Librarian is responsible for parsing files and outputting the final journal.
    We use internal class methods to check proper handling of data throughout the process.
    """

    @pytest.fixture
    def valid_librarian(self):
        """Fixture providing a Librarian instance without custom moods."""
        return Librarian(path_to_file=str(RESOURCES / "journals/all-valid.csv"))

    @pytest.fixture
    def valid_librarian_custom_moods(self):
        """Fixture providing a Librarian instance with custom moods."""
        return Librarian(
            path_to_file=str(RESOURCES / "journals/all-valid.csv"),
            path_to_moods=str(RESOURCES / "moods/all-valid-moods.json")
        )

    # generates this many unique librarians with wrong CSVs
    @pytest.fixture(params=[
        "corrupted.csv",
        "wrong-format.txt",
        "missing.csv",
        "empty.csv",
    ])
    def invalid_librarian(self, request):
        return lambda: Librarian(path_to_file=str(RESOURCES / "journals" / request.param))

    # --------------------------------------

    def test_init_valid_csv(self, valid_librarian):
        assert valid_librarian

    def test_init_invalid_csv(self, invalid_librarian):
        """Pass faulty files and see if it fails as expected."""
        with pytest.raises(CannotAccessJournalError):
            assert invalid_librarian

        # TODO: what to do with no extension file?
        # TODO: handle this case in Librarian

        # TODO: maybe generate corrupted_sheet and wrong_format during runner setup in workflow mode?
        # dd if=/dev/urandom of="$corrupted_file" bs=1024 count=10
        # generates random bytes and writes them into a given file

        # TODO: move check locked file test into Docker run

    @pytest.mark.parametrize("valid_date", [
        "2022-10-25",
        "2022-10-26",
        "2022-10-27",
        "2022-10-30",
    ])
    def test_valid_access_dates(self, valid_date):
        """
        All the following dates exist in the ``tests/files/all-valid.csv``.
        They should be accessible by ``lib``.
        """
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods="all-valid.json"
        )

        assert lib[valid_date]

    @pytest.mark.parametrize("invalid_date", [
        "2022-10-21",
        "2022-10-20",
        "2022-10-2",
        "1999-10-22",
    ])
    def test_wrong_access_dates_key_error(self, invalid_date):
        """
        **None** of the following dates exist in the ``tests/files/all-valid.csv``.
        Therefore, they should **NOT** be accessible by ``lib``.
        """
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods="all-valid.json"
        )

        with pytest.raises(KeyError):
            _ = lib[invalid_date]

    @pytest.mark.parametrize("invalid_format", [
        "ABC",
        "2022",
        "12:00 AM",

        # Empty / whitespace
        "",
        " ",
        "   ",

        # Wrong separators / order
        "2022/13/01",
        "01-2022-12",
        "2022.12.01",
        "12/01/22",

        # Impossible dates
        "2022-02-30",
        "2022-04-31",
        "2022-13-01",
        "2022-00-10",
        "2022-01-00",

        # Partial dates
        "2022-01",
        # "2022-01-1",
        # "2022-1-01",

        # Time mixed in
        "2022-01-01 12:00",
        "2022-01-01T25:00:00",
        "2022-01-01T12:60:00",

        # Non-date but numeric
        # "123456", -- TODO: fucking fix these instead of commenting them out - why are they considered valid?
        "0000-00-00",

        # Locale / text noise
        "Jan 1, 2022",
        "01 Jan 2022",
        "today",
        "yesterday",
    ])
    def test_wrong_access_dates_value_error(self, invalid_format):
        """Check if Librarian correctly raises ValueError when trying to check invalid dates."""
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "all-valid-moods.json")
        )

        with pytest.raises(ValueError):
            _ = lib[invalid_format]

    # CUSTOM AND STANDARD MOOD SETS
    # -----------------------------
    def test_custom_moods_when_passed_correctly(self):
        """Pass a valid JSON file and see if it knows it has access to custom moods now."""
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "all-valid-moods.json")
        )
        assert lib.mood_set.get_custom_moods

    def test_custom_moods_when_not_passed(self):
        """Pass no moods and see if it know it only has standard moods available."""
        lib = Librarian(path_to_file=str(RESOURCES / "all-valid-entries.csv"))
        assert len(lib.mood_set.get_custom_moods) == 0, str(lib.mood_set)

    def test_custom_moods_with_invalid_jsons(self):
        """Pass faulty moods and see if it has no custom moods loaded."""
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "empty.csv")
        )
        assert len(lib.mood_set.get_custom_moods) == 0

    def test_custom_moods_when_json_invalid(self):
        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "empty.csv")
        )
        default = Moodverse()

        assert lib.mood_set.get_moods == default.get_moods, (
            f"current ID:\t{id(lib.mood_set)}\n"
            f"default object ID:\t{id(default)}"
        )

        lib = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "empty.csv")
        )
        assert lib.mood_set.get_moods == default.get_moods, (
            f"current ID:\t{id(lib.mood_set)}\n"
            f"default object ID:\t{id(default)}"
        )

        # TODO: move locked folder and locked file tests into Docker run
        assert lib.mood_set.get_moods == default.get_moods, (
            f"current ID:\t{id(lib.mood_set)}\n"
            f"default object ID:\t{id(default)}"
        )

    def test_custom_moods_that_are_incomplete(self):
        """
        Moodverse can deal with incomplete moods because the file merely expands its default knowledge.
        However, it can only expand it (and be truthy) if the dict with moods has all required groups.
        Therefore, since ``incomplete-moods`` lacks the ``good`` group, the assertion will evaluate to False.
        """
        custom_config = EntriesFromBuilder(entries_builder=EntryBuilder(tag_activities=True))
        lib_to_test = Librarian(
            path_to_file=str(RESOURCES / "all-valid-entries.csv"),
            path_to_moods=str(RESOURCES / "incomplete-moods.json"),
            entries_from_builder=custom_config
        )
        # There are 11 moods, out of which one is a duplicate of a default mood, so 10 custom in total
        assert len(lib_to_test.mood_set.get_custom_moods) == 10, \
            str(lib_to_test.mood_set.get_custom_moods.keys())




# Example of using fixtures for cleaner tests
class TestLibrarianWithFixtures:

    @pytest.mark.parametrize("date", ["2022-10-25", "2022-10-26", "2022-10-27", "2022-10-30"])
    def test_valid_dates_with_valid_librarians(self, valid_librarian, date):
        """Test accessing valid dates using fixture."""
        assert valid_librarian[date]

    def test_has_custom_moods(self, valid_librarian):
        """Test that fixture has custom moods loaded."""
        assert valid_librarian.mood_set.get_custom_moods

    def test_no_custom_moods(self, valid_librarian_without_custom_moods):
        """Test that fixture has no custom moods."""
        assert len(valid_librarian_without_custom_moods.mood_set.get_custom_moods) == 0