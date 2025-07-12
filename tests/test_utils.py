import logging
import datetime
from unittest import TestCase

from daylio_to_md import utils
from daylio_to_md.utils import guess_time_type, guess_date_type


class TestSlugify(TestCase):
    def test_slugify(self):
        # no need to check if slug is a valid tag
        # noinspection SpellCheckingInspection
        self.assertEqual("convertthis-to-a-slug", utils.slugify("ConvertThis to-------a SLUG", False))
        # noinspection SpellCheckingInspection
        self.assertEqual("zażółć-gęślą-jaźń", utils.slugify("Zażółć gęślą jaźń    ", False))
        self.assertEqual("multiple-spaces-between-words", utils.slugify("  Multiple   spaces  between    words", False))
        # noinspection SpellCheckingInspection
        self.assertEqual("хлеба-нашего-повшеднего", utils.slugify("Хлеба нашего повшеднего", False))

        # check if the slug is a valid tag
        with self.assertLogs(logging.getLogger("daylio_to_md.utils"), logging.WARNING):
            utils.slugify("1. Digit cannot appear at the beginning of a tag", True)

        current_logger = logging.getLogger("daylio_to_md.utils")
        with self.assertLogs(current_logger, logging.WARNING) as logs:
            # We want to assert there are no warnings, but the 'assertLogs' method does not support that.
            # Therefore, we are adding a dummy warning, and then we will assert it is the only warning.
            current_logger.warning("Dummy warning")
            utils.slugify("Digits within the string 1234 - are ok", True)
            utils.slugify("Digits at the end of the string are also ok 456", True)
        # assertLogs.output is a list of strings containing formatted logs, so len() == 0 is noLogs
        # I refrain from using assertNoLogs because that bumps Python version requirement to 3.10
        # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertNoLogs
        self.assertListEqual(["WARNING:daylio_to_md.utils:Dummy warning"], logs.output)


class TestExpandPath(TestCase):
    def test_expand_path(self):
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path("$HOME/whatever").startswith("$HOME"))
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path('~/yes').startswith('~'))


class TestStripping(TestCase):
    def test_strip_and_get_truthy(self):
        self.assertListEqual(["one", "two"], utils.strip_and_get_truthy("\"one||two|||||\"", "|"))
        self.assertListEqual([], utils.strip_and_get_truthy("\"\"", "|"))


class TestSlicing(TestCase):
    def test_slice_quotes(self):
        self.assertEqual("test", utils.slice_quotes("\"test\""))
        self.assertIsNone(utils.slice_quotes("\"\""))
        self.assertEqual("bicycle", utils.slice_quotes("\" bicycle   \""))


class TestIOContextManager(TestCase):
    def testJsonContextManager(self):
        expected_dict = {'rad': ['rad'], 'good': ['good'], 'neutral': ['okay'], 'bad': ['bad'], 'awful': ['awful']}
        with utils.JsonLoader().load('tests/files/moods/smallest.json') as example_file:
            self.assertDictEqual(expected_dict, example_file)

    def testCsvContextManager(self):
        with utils.CsvLoader().load('tests/files/all-valid.csv') as example_file:
            expected_dict = {
                'full_date': '2022-10-30',
                'date': 'October 30',
                'weekday': 'Sunday',
                'time': '10:04 AM',
                'mood': 'vaguely ok',
                'activities': '2ćities  skylines | dó#lóó fa$$s_ą%',
                'note_title': 'Dolomet',
                'note': 'Lorem ipsum sit dolomet amęt.'
            }
            # next() loads the first contentful line after csv column names
            self.assertDictEqual(expected_dict, next(example_file))


class TestDateTimeGuessing(TestCase):
    def test_12_hour_format(self):
        self.assertEqual(guess_time_type("02:30 PM"), datetime.time(14, 30))
        self.assertEqual(guess_time_type("12:00 AM"), datetime.time(0, 0))
        self.assertEqual(guess_time_type("12:00 PM"), datetime.time(12, 0))

    def test_24_hour_format(self):
        self.assertEqual(guess_time_type("14:30"), datetime.time(14, 30))
        self.assertEqual(guess_time_type("00:00"), datetime.time(0, 0))
        self.assertEqual(guess_time_type("23:59"), datetime.time(23, 59))

    def test_no_leading_zero(self):
        self.assertEqual(guess_time_type("2:30 PM"), datetime.time(14, 30))
        self.assertEqual(guess_time_type("2:30"), datetime.time(2, 30))

    def test_list_input(self):
        self.assertEqual(guess_time_type([14, 30]), datetime.time(14, 30))
        self.assertEqual(guess_time_type([0, 0]), datetime.time(0, 0))
        self.assertEqual(guess_time_type([23, 59]), datetime.time(23, 59))

    def test_time_object_input(self):
        self.assertEqual(guess_time_type(datetime.time(14, 30)), datetime.time(14, 30))
        self.assertEqual(guess_time_type(datetime.time(0, 0)), datetime.time(0, 0))

    def test_edge_cases(self):
        self.assertEqual(guess_time_type("11:59 PM"), datetime.time(23, 59))
        self.assertEqual(guess_time_type("12:01 AM"), datetime.time(0, 1))

    def test_invalid_inputs(self):
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type("25:00")
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type("14:60")
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type("2:30 ZM")
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type([14, 30, 0])
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type([14])
        with self.assertRaises(utils.InvalidTimeError):
            guess_time_type("not a time")

    def test_string_variations(self):
        self.assertEqual(guess_time_type("2:30PM"), datetime.time(14, 30))
        self.assertEqual(guess_time_type("2:30 pm"), datetime.time(14, 30))
        self.assertEqual(guess_time_type("02:30pm"), datetime.time(14, 30))

    def test_whitespace_handling(self):
        self.assertEqual(guess_time_type("  14:30  "), datetime.time(14, 30))
        self.assertEqual(guess_time_type("2:30 PM  "), datetime.time(14, 30))


class TestGuessDateType(TestCase):
    def test_string_input(self):
        self.assertEqual(guess_date_type("2023-05-15"), datetime.date(2023, 5, 15))
        self.assertEqual(guess_date_type("2000-01-01"), datetime.date(2000, 1, 1))
        self.assertEqual(guess_date_type("2099-12-31"), datetime.date(2099, 12, 31))
        self.assertEqual(guess_date_type("2023-5-15"), datetime.date(2023, 5, 15))
        self.assertEqual(guess_date_type(["2023", "05", "15"]), datetime.date(2023, 5, 15))

    def test_list_input(self):
        self.assertEqual(guess_date_type([2023, 5, 15]), datetime.date(2023, 5, 15))
        self.assertEqual(guess_date_type([2000, 1, 1]), datetime.date(2000, 1, 1))
        self.assertEqual(guess_date_type([2099, 12, 31]), datetime.date(2099, 12, 31))

    def test_date_object_input(self):
        test_date = datetime.date(2023, 5, 15)
        self.assertEqual(guess_date_type(test_date), test_date)

    def test_edge_cases(self):
        # Leap year
        self.assertEqual(guess_date_type("2024-02-29"), datetime.date(2024, 2, 29))
        # Year boundaries
        self.assertEqual(guess_date_type([1, 1, 1]), datetime.date(1, 1, 1))
        self.assertEqual(guess_date_type("9999-12-31"), datetime.date(9999, 12, 31))

    def test_invalid_list_input(self):
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type([2023, 5])  # Too few elements
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type([2023, 5, 15, 12])  # Too many elements
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type([2023, 13, 1])  # Invalid month
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type([2023, 2, 30])  # Invalid day for February

    def test_list_with_mixed_type(self):
        self.assertEqual(guess_date_type(["2023", 5, "15"]), datetime.date(2023, 5, 15))

    def test_invalid_string_format(self):
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type("2023/05/15")
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type("15-05-2023")

    # noinspection PyTypeChecker
    def test_invalid_types(self):
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type(20230515)  # Integer input
        with self.assertRaises(utils.InvalidDateError):
            guess_date_type({"year": 2023, "month": 5, "day": 15})  # Dictionary input

    def test_string_with_whitespace(self):
        self.assertEqual(guess_date_type("  2023-05-15  "), datetime.date(2023, 5, 15))
