import logging
from unittest import TestCase

from src import utils


class TestUtils(TestCase):
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
        with self.assertLogs(logging.getLogger("src.utils"), logging.WARNING):
            utils.slugify("1. Digit cannot appear at the beginning of a tag", True)

        with self.assertNoLogs(logging.getLogger("src.utils"), logging.WARNING):
            utils.slugify("Digits within the string 1234 - are ok", True)

        with self.assertNoLogs(logging.getLogger("src.utils"), logging.WARNING):
            utils.slugify("Digits at the end of the string are also ok 456", True)

    def test_expand_path(self):
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path("$HOME/whatever").startswith("$HOME"))
        # noinspection SpellCheckingInspection
        self.assertFalse(utils.expand_path('~/yes').startswith('~'))
