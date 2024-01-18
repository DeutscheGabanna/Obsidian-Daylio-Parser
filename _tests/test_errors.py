from unittest import TestCase

import errors


class TestErrorMsgBase(TestCase):
    def test_print(self):
        # All arguments correctly passed
        self.assertIsInstance(
            errors.ErrorMsgBase.print(errors.ErrorMsgBase.WRONG_VALUE, "x", "y"),
            str,
            msg="The function should return a string.")
        # Missing argument
        self.assertEqual(
            errors.ErrorMsgBase.print(errors.ErrorMsgBase.WRONG_VALUE, "y"),
            None,
            msg="The function should complain it has not received enough arguments to complete the error message")
