from unittest import TestCase

import tests.suppress as suppress
from daylio_to_md.entry.mood import Moodverse, MoodNotFoundError


# noinspection SpellCheckingInspection
class TestMoodverse(TestCase):
    @suppress.out
    def test_default_moodverse_no_customisation(self):
        self.assertDictEqual(
            {"rad": "rad", "good": "good", "neutral": "neutral", "bad": "bad", "awful": "awful"},
            Moodverse().get_moods
        )
        self.assertFalse(Moodverse().get_custom_moods)
        self.assertEqual("rad", Moodverse()["rad"])
        self.assertEqual("bad", Moodverse()["bad"])
        with self.assertRaises(MoodNotFoundError):
            # noinspection PyStatementEffect
            Moodverse()["amazing"]
        # don't compare Moodverses by their memory address, but by their contents
        self.assertEqual(Moodverse(), Moodverse())

    @suppress.out
    def test_loading_valid_moods_into_moodverse(self):
        # These moods are self-sufficient, because even if standard mood set didn't exist, they satisfy all requirements
        ok_moods_loaded_from_json = {
            "rad": ["rad", "amazing"],
            "good": ["good", "nice"],
            "neutral": ["neutral", "ok", "fine"],
            "bad": ["bad"],
            "awful": ["awful", "miserable"]
        }
        my_moodverse = Moodverse(ok_moods_loaded_from_json)

        self.assertNotEqual(
            {"rad": "rad", "good": "good", "neutral": "neutral", "bad": "bad", "awful": "awful"},
            my_moodverse.get_moods
        )
        # in total there are 10 moods, but there are only 5 additional moods if you skip duplicates from defaults
        self.assertEqual(5, len(my_moodverse.get_custom_moods))
        self.assertIn("nice", my_moodverse.get_moods)
        self.assertIn("amazing", my_moodverse.get_moods)
        self.assertIn("miserable", my_moodverse.get_moods)

        self.assertIn("neutral", Moodverse().get_moods)
        self.assertIn("bad", Moodverse().get_moods)
        self.assertIn("awful", Moodverse().get_moods)
        self.assertIn("good", Moodverse().get_moods)
        self.assertIn("rad", Moodverse().get_moods)

        with self.assertRaises(MoodNotFoundError):
            # noinspection PyStatementEffect
            Moodverse()["terrific"]

    # noinspection PyStatementEffect
    @suppress.out
    def test_loading_moodsets_with_unknown_keys(self):
        # This mood set contains unknown mood groups. They should be skipped.
        moodlist_with_unknown_group = {
            "holy cow": ["badger", "fox", "falcon"],  # unknown group
            "rad": ["amazing"],
            "good": ["nice"],
            "neutral": ["ok", "fine"],
            "bad": ["bad"],
            "awful": ["miserable"]
        }

        my_moodverse = Moodverse(moodlist_with_unknown_group)
        # There are 9 moods on the list, 8 non-standard ones. Should be less than 8 because we skip 3 from "holy cow".
        self.assertEqual(len(my_moodverse.get_custom_moods), 5, msg=my_moodverse.get_custom_moods.keys())
        # Standard moods should still be in the groups, irrespective of what was in the custom dictionary
        self.assertIn("rad", my_moodverse.get_moods)
        self.assertIn("good", my_moodverse.get_moods)
        self.assertIn("awful", my_moodverse.get_moods)
        self.assertIn("neutral", my_moodverse.get_moods)
        with self.assertRaises(MoodNotFoundError):
            my_moodverse["badger"]
        with self.assertRaises(MoodNotFoundError):
            my_moodverse["fox"]
        with self.assertRaises(MoodNotFoundError):
            my_moodverse["falcon"]

    @suppress.out
    def test_loading_incomplete_moodlists(self):
        moodlist_incomplete = {
            "awful": ["miserable"]
        }

        my_moodverse = Moodverse(moodlist_incomplete)
        self.assertGreater(len(my_moodverse.get_custom_moods), 0)
        self.assertIn("miserable", my_moodverse.get_moods)
        self.assertIn("awful", my_moodverse.get_moods)
        self.assertIn("good", my_moodverse.get_moods)

    def test_loading_invalid_moodlists(self):
        bad_moods_loaded_from_json = {
            "rad": ["", None],
            "good": [""],
            "neutral": ["", 15],
            "bad": ["", True],
            "awful": [""]
        }
        self.assertEqual(0, len(Moodverse(bad_moods_loaded_from_json).get_custom_moods))

        bad_moods_loaded_from_json = {
            "rad": ["rad"],
            "good": ["good"],
            "neutral": ["neutral"],
            "bad": ["bed"],
            "awful": [""]  # <--
        }
        self.assertEqual(1, len(Moodverse(bad_moods_loaded_from_json).get_custom_moods))
