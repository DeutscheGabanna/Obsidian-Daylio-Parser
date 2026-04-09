import unittest
from unittest import TestCase

from obsidian_daylio_parser import config


reason = """
Argument handling is done by Typer library.
These types of tests should focus on checking the behavior of the program
when it receives certain arguments, not on testing the argument parsing itself.
"""

class TestSettingsManager(TestCase):
    def test_spoofed_keyword_option_without_equality_sign(self):
        unittest.SkipTest(reason)

    def test_spoofed_keyword_option_with_equality_sign(self):
        unittest.SkipTest(reason)

    def test_check_if_required_arguments_passed(self):
        unittest.SkipTest(reason)

    def test_expected_failure_empty_argument_array(self):
        unittest.SkipTest(reason)