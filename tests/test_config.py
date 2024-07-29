from unittest import TestCase

import tests.suppress as suppress
from daylio_to_md import config


class TestSettingsManager(TestCase):
    @suppress.out
    def test_spoofed_keyword_option_without_equality_sign(self):
        """
        In this case, SettingsManager can receive either "--force accept", "--force refuse" or None as prog arguments.
        Check if it behaves properly with various user inputs as console arguments.
        """
        # foo and bar is there as first two elements because they are fake filepath and fake destination
        # User input not in the dictionary of allowed options - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console(["foo", "bar", "--force", "yo-mama"])
        self.assertEqual(2, cm.exception.code, msg="Invalid arguments were passed to argparse so it should exit with 2")

        # User input provided both options - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console(["foo", "bar", "--force", "refuse", "accept"])
        self.assertEqual(2, cm.exception.code, msg="Cannot both force-refuse and force-accept - should exit with 2")

        # User input correct - should pass
        config.parse_console(["foo", "bar", "--force", "refuse"])
        config.parse_console(["foo", "bar", "--force", "accept"])

    @suppress.out
    def test_spoofed_keyword_option_with_equality_sign(self):
        """
        In this case, SettingsManager can receive either "--force=accept", "--force=refuse" or None as prog arguments.
        Check if it behaves properly with various user inputs as console arguments.
        """
        # User input not in the dictionary of allowed options - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console(["foo", "bar", "--force=yo-mama"])
        self.assertEqual(2, cm.exception.code, msg="Invalid arguments were passed to argparse so it should exit with 2")

        # User input provided both options - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console(["foo", "bar", "--force=refuse --force=accept"])
        self.assertEqual(2, cm.exception.code, msg="Cannot both force-refuse and force-accept - should exit with 2")

        # User input correct - should pass
        this_config = config.parse_console(["foo", "bar", "--force=refuse"])
        self.assertEqual("refuse", this_config.force)

        # User input correct - should pass
        this_config = config.parse_console(["foo", "bar", "--force=accept"])
        self.assertEqual("accept", this_config.force)

    @suppress.out
    def test_check_if_required_arguments_passed(self):
        # User did not provide the required argument - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console(["--optional_arg", "haha"])
        self.assertEqual(2, cm.exception.code, msg="No filepath provided - should exit with 2")

        # User input correct - should pass
        this_config = config.parse_console(["wakanda", "forever"])
        self.assertEqual("wakanda", this_config.filepath)
        self.assertEqual("forever", this_config.destination)

    @suppress.out
    def test_expected_failure_empty_argument_array(self):
        # User provided no arguments whatsoever - should fail
        with self.assertRaises(SystemExit) as cm:
            config.parse_console([])
        self.assertEqual(2, cm.exception.code, msg="No arguments provided to argparse so it should exit with 2")
