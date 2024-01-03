from unittest import TestCase
from config import options


class TestSettingsManager(TestCase):
    def setUp(self) -> None:
        self.librarian_settings = options.get_console().add_argument_group(
            "Librarian",
            "Handles main options"
        )
        self.librarian_settings.add_argument(
            "filepath",
            type=str,
            help="Specify path to the .CSV file"
        )
        self.librarian_settings.add_argument(
            "destination",
            default="",
            type=str,
            help="Path to folder to output finished files into."
        )
        self.filepath_to_check = "_tests/sheet-1-valid-data.csv"
        self.destination_to_check = "somewhere"
        self.force_option_to_check = "accept"

    def test_spoofed_librarian_settings_without_equality_sign(self):
        options.parse_spoofed_console([
            self.filepath_to_check,
            self.destination_to_check,
            "--force", self.force_option_to_check])
        self.assertEqual(options.settings.filepath, self.filepath_to_check)
        self.assertEqual(options.settings.destination, self.destination_to_check)
        self.assertEqual(options.settings.force, self.force_option_to_check)

    def test_spoofed_librarian_settings_with_equality_sign(self):
        options.parse_spoofed_console([
            self.filepath_to_check,
            self.destination_to_check,
            "--force=" + self.force_option_to_check])
        self.assertEqual(options.settings.filepath, self.filepath_to_check)
        self.assertEqual(options.settings.destination, self.destination_to_check)
        self.assertEqual(options.settings.force, self.force_option_to_check)

    def test_expected_failure_empty_argument_array(self):
        with self.assertRaises(SystemExit) as cm:
            options.parse_spoofed_console([])
        self.assertEqual(cm.exception.code, 2, msg="Invalid arguments were passed to argparse so it should exit with 2")

    def test_expected_failure_outside_of_dictionary(self):
        with self.assertRaises(SystemExit) as cm:
            # noinspection SpellCheckingInspection
            options.parse_spoofed_console(
                [self.filepath_to_check,
                 self.destination_to_check,
                 "--force",
                 "yabadoo"])
        self.assertEqual(cm.exception.code, 2, msg="Invalid arguments were passed to argparse so it should exit with 2")
