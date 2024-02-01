from unittest import TestCase

from src import config


class TestSettingsManager(TestCase):
    def test_spoofed_keyword_option_without_equality_sign(self):
        """
        In this case, SettingsManager can receive either "--force accept", "--force refuse" or None as prog arguments.
        Check if it behaves properly with various user inputs as console arguments.
        """
        # Setup
        options_to_check = config.SettingsManager()
        options_to_check.arg_console.add_argument(
            "--force",
            choices=["accept", "refuse"],
            default=None
        )

        # User input not in the dictionary of allowed options - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console(["--force", "yo-mama"])
        self.assertEqual(cm.exception.code, 2, msg="Invalid arguments were passed to argparse so it should exit with 2")

        # User input provided both options - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console(["--force", "refuse", "accept"])
        self.assertEqual(cm.exception.code, 2, msg="Cannot both force-refuse and force-accept - should exit with 2")

        # User input correct - should pass
        options_to_check.parse_console(["--force", "refuse"])
        options_to_check.parse_console(["--force", "accept"])

    def test_spoofed_keyword_option_with_equality_sign(self):
        """
        In this case, SettingsManager can receive either "--force=accept", "--force=refuse" or None as prog arguments.
        Check if it behaves properly with various user inputs as console arguments.
        """
        # Setup
        options_to_check = config.SettingsManager()
        options_to_check.arg_console.add_argument(
            "--force",
            choices=["accept", "refuse"],
            default=None
        )

        # User input not in the dictionary of allowed options - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console(["--force=yo-mama"])
        self.assertEqual(cm.exception.code, 2, msg="Invalid arguments were passed to argparse so it should exit with 2")

        # User input provided both options - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console(["--force=refuse --force=accept"])
        self.assertEqual(cm.exception.code, 2, msg="Cannot both force-refuse and force-accept - should exit with 2")

        # User input correct - should pass
        options_to_check.parse_console(["--force=refuse"])
        self.assertEqual(options_to_check.force, "refuse")

        # User input correct - should pass
        options_to_check.parse_console(["--force=accept"])
        self.assertEqual(options_to_check.force, "accept")

    def test_check_if_required_arguments_passed(self):
        # Setup
        options_to_check = config.SettingsManager()
        options_to_check.arg_console.add_argument(
            "filepath",
            type=str
        )
        options_to_check.arg_console.add_argument(
            "--optional_arg",
            type=str
        )

        # User did not provide the required argument - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console(["--optional_arg", "haha"])
            print(options_to_check)
        self.assertEqual(cm.exception.code, 2, msg="No filepath provided - should exit with 2")

        # User input correct - should pass
        options_to_check.parse_console(["wakanda forever"])
        self.assertEqual(options_to_check.filepath, "wakanda forever")

    def test_expected_failure_empty_argument_array(self):
        # Setup
        options_to_check = config.SettingsManager()
        options_to_check.arg_console.add_argument(
            "filepath",
            type=str
        )

        # User provided no arguments whatsoever - should fail
        with self.assertRaises(SystemExit) as cm:
            options_to_check.parse_console([])
        self.assertEqual(cm.exception.code, 2, msg="No arguments provided to argparse so it should exit with 2")

    # TODO: test Namespace=self where SettingsManager overwrites its default attributes with argparse
    def test_if_settings_manager_overwrites_its_properties_from_console(self):
        """
        SettingsManager has default attributes as options already at instantiation.
        This test case checks if the argparse can correctly overwrite these default attributes with its own.
        """
        # Setup
        options_to_check = config.SettingsManager()
        options_to_check.filepath = "this is the default value"

        options_to_check.arg_console.add_argument(
            "filepath",
            type=str
        )
        options_to_check.arg_console.add_argument(
            "foo",
            type=str,
            help="this type of argument does not appear in the SettingsManager list of attributes at setup"
        )
        options_to_check.arg_console.add_argument(
            "bar",
            type=str,
            help="this type of argument does not appear in the SettingsManager list of attributes at setup"
        )

        # User input correct - should pass
        options_to_check.parse_console(["this is NOT the default value", "hello", "world"])
        self.assertEqual(options_to_check.filepath, "this is NOT the default value")
        self.assertNotEqual(options_to_check.filepath, "this is the default value")
        # because neither "foo" nor "bar" is part of the SettingsManager class, I need to access it like a key in dict
        self.assertEqual(vars(options_to_check)["foo"], "hello")
        self.assertEqual(vars(options_to_check)["bar"], "world")
