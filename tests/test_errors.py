from unittest import TestCase

from obsidian_daylio_parser import errors, logs


class TestErrorMsgBase(TestCase):
    def test_print(self):
        # All arguments correctly passed
        self.assertIsInstance(
            logs.LogMsg.print(logs.LogMsg.WRONG_VALUE, "x", "y"),
            str,
            msg="The function should return a string.")
        # Missing argument
        self.assertEqual(
            logs.LogMsg.print(logs.LogMsg.WRONG_VALUE, "y"),
            None,
            msg="The function should complain it has not received enough arguments to complete the error message")
