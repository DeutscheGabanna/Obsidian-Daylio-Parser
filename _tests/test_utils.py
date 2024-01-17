import os.path
from unittest import TestCase
import logging
import utils


class TestUtils(TestCase):
    def test_slugify(self):
        # no need to check if slug is a valid tag
        # noinspection SpellCheckingInspection
        self.assertEqual(utils.slugify("ConvertThis to-------a SLUG", False), "convertthis-to-a-slug")
        # noinspection SpellCheckingInspection
        self.assertEqual(utils.slugify("Zażółć gęślą jaźń    ", False), "zażółć-gęślą-jaźń")
        self.assertEqual(utils.slugify("  Multiple   spaces  between    words", False), "multiple-spaces-between-words")
        # noinspection SpellCheckingInspection
        self.assertEqual(utils.slugify("Хлеба нашего повшеднего", False), "хлеба-нашего-повшеднего")

        # check if the slug is a valid tag
        with self.assertLogs(logging.getLogger("utils"), logging.WARNING):
            utils.slugify("1. Digit cannot appear at the beginning of a tag", True)

        with self.assertNoLogs(logging.getLogger("utils"), logging.WARNING):
            utils.slugify("Digits within the string 1234 - are ok", True)

        with self.assertNoLogs(logging.getLogger("utils"), logging.WARNING):
            utils.slugify("Digits at the end of the string are also ok 456", True)

    def test_expand_path(self):
        # noinspection SpellCheckingInspection
        self.assertEqual(utils.expand_path("$HOME/whatever"), "/home/deutschegabanna/whatever")
        # noinspection SpellCheckingInspection
        self.assertEqual(utils.expand_path('~/yes'), "/home/deutschegabanna/yes")
