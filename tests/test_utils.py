import logging
from unittest import TestCase

import tests.suppress as suppress
from daylio_to_md import utils


class TestUtils(TestCase):
    @suppress.out
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

    @suppress.out
    def test_expand_path(self):
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path("$HOME/whatever").startswith("$HOME"))
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path('~/yes').startswith('~'))

    @suppress.out
    def test_strip_and_get_truthy(self):
        self.assertListEqual(["one", "two"], utils.strip_and_get_truthy("\"one||two|||||\"", "|"))
        self.assertListEqual([], utils.strip_and_get_truthy("\"\"", "|"))

    @suppress.out
    def test_slice_quotes(self):
        self.assertEqual("test", utils.slice_quotes("\"test\""))
        self.assertIsNone(utils.slice_quotes("\"\""))
        self.assertEqual("bicycle", utils.slice_quotes("\" bicycle   \""))


class TestIOContextManager(TestCase):
    @suppress.out
    def testJsonContextManager(self):
        expected_dict = {'rad': ['rad'], 'good': ['good'], 'neutral': ['okay'], 'bad': ['bad'], 'awful': ['awful']}
        with utils.JsonLoader().load('tests/files/mood_JSONs/smallest_moodset_possible.json') as example_file:
            self.assertDictEqual(expected_dict, example_file)

    @suppress.out
    def testCsvContextManager(self):
        with utils.CsvLoader().load('tests/files/journal_CSVs/sheet-1-valid-data.csv') as example_file:
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
