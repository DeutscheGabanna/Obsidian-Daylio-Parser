import logging
from unittest import TestCase

from src.entry.mood import \
    Moodverse, \
    MoodGroup


# noinspection SpellCheckingInspection
class TestMoodverse(TestCase):
    def test_default_moodverse_no_customisation(self):
        my_default_moodverse = Moodverse()
        self.assertTrue(isinstance(my_default_moodverse["rad"], MoodGroup))
        self.assertTrue(isinstance(my_default_moodverse["good"], MoodGroup))
        self.assertTrue(isinstance(my_default_moodverse["neutral"], MoodGroup))
        self.assertTrue(isinstance(my_default_moodverse["bad"], MoodGroup))
        self.assertTrue(isinstance(my_default_moodverse["awful"], MoodGroup))

        self.assertEqual(["rad"], my_default_moodverse["rad"])
        self.assertEqual(["good"], my_default_moodverse["good"])
        self.assertEqual(["neutral"], my_default_moodverse["neutral"])
        self.assertEqual(["bad"], my_default_moodverse["bad"])
        self.assertEqual(["awful"], my_default_moodverse["awful"])

        # this is just so I can test whether my __eq__ function overload correctly skips this
        self.assertNotEqual(my_default_moodverse["awful"], MoodGroup("awful"))

        # These comparisons should be falsy because the array has more moods than the default mood set initialised
        self.assertNotEqual(["rad", "amazing"], my_default_moodverse["rad"])
        self.assertNotEqual(["awful", "miserable"], my_default_moodverse["awful"])

        # This comparison should be falsy because it does not contain the default mood set initialised
        # └── known moods of 'neutral' group
        #     └── neutral <-- from standard
        # And we're basically saying, "In neutral group there should only be a 'meh' mood"
        self.assertNotEqual(["meh"], my_default_moodverse["neutral"])

    def test_loading_valid_moods_into_moodverse(self):
        # These moods are self-sufficient, because even if standard mood set didn't exist, they satisfy all requirements
        ok_moods_loaded_from_json = {
            "rad":
                ["rad", "amazing"],
            "good":
                ["good", "nice"],
            "neutral":
                ["neutral", "ok", "fine"],
            "bad":
                ["bad"],
            "awful":
                ["awful", "miserable"]
        }
        my_moodverse = Moodverse(ok_moods_loaded_from_json)
        self.assertTrue(isinstance(my_moodverse["rad"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["good"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["neutral"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["bad"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["awful"], MoodGroup))

        self.assertEqual(["rad", "amazing"], my_moodverse["rad"])
        self.assertEqual(["good", "nice"], my_moodverse["good"])
        self.assertEqual(["neutral", "ok", "fine"], my_moodverse["neutral"])
        self.assertEqual(["bad"], my_moodverse["bad"])
        self.assertEqual(["awful", "miserable"], my_moodverse["awful"])

    def test_loading_semi_valid_moods_into_moodverse(self):
        # This mood set isn't self-sufficient, but still valid, because it has all the required "groups".
        # Standard mood set is used here to cover for missing moods
        # so, when:
        semi_ok_moods_loaded_from_json = {
            "rad":
                ["amazing"],  # lacks rad
            "good":
                ["nice"],  # lacks good
            "neutral":
                ["ok", "fine"],  # lacks neutral
            "bad":
                ["bad"],  # OK
            "awful":
                ["miserable"]  # lacks awful
        }

        # then I can still use my moodverse, because standard set filled the blanks like so:
        # .
        # ├── known moods of 'rad' group
        # │   └── rad <-- from standard
        # │   └── amazing
        # ├── known moods of 'great' group
        # │   └── great <-- from standard
        # │   └── nice
        # ├── known moods of 'neutral' group
        # │   └── neutral <-- from standard
        # │   └── ok
        # │   └── fine
        # ├── known moods of 'bad' group
        # │   └── bad
        # └── known moods of 'awful' group
        #     └── awful <0 from standard
        #     └── miserable

        my_moodverse = Moodverse(semi_ok_moods_loaded_from_json)
        self.assertTrue(isinstance(my_moodverse["rad"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["good"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["neutral"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["bad"], MoodGroup))
        self.assertTrue(isinstance(my_moodverse["awful"], MoodGroup))

        # responses should be identical to the ones in previous test, because standard mood filled the blanks
        self.assertEqual(["rad", "amazing"], my_moodverse["rad"])
        self.assertEqual(["good", "nice"], my_moodverse["good"])
        self.assertEqual(["neutral", "ok", "fine"], my_moodverse["neutral"])
        self.assertEqual(["bad"], my_moodverse["bad"])
        self.assertEqual(["awful", "miserable"], my_moodverse["awful"])

        # let's shuffle the order of values around to check if both lists are still equal
        self.assertEqual(["amazing", "rad"], my_moodverse["rad"])
        self.assertEqual(["nice", "good"], my_moodverse["good"])
        self.assertEqual(["ok", "neutral", "fine"], my_moodverse["neutral"])
        self.assertEqual(["bad"], my_moodverse["bad"])
        self.assertEqual(["miserable", "awful"], my_moodverse["awful"])

    def test_get_mood(self):
        # These moods are self-sufficient, because even if standard mood set didn't exist, they satisfy all requirements
        ok_moods_loaded_from_json = {
            "rad":
                ["rad", "amazing", "awesome"],
            "good":
                ["good", "nice", "great"],
            "neutral":
                ["neutral", "ok", "fine", "whatever"],
            "bad":
                ["bad", "tired"],
            "awful":
                ["awful", "miserable"]
        }

        query_moodverse = Moodverse(ok_moods_loaded_from_json)
        self.assertTrue(query_moodverse.get_mood("fine"))
        self.assertTrue(query_moodverse.get_mood("tired"))
        self.assertTrue(query_moodverse.get_mood("miserable"))
        self.assertTrue(query_moodverse.get_mood("amazing"))
        self.assertTrue(query_moodverse.get_mood("bad"))

        self.assertFalse(query_moodverse.get_mood("horrible"))
        self.assertFalse(query_moodverse.get_mood("disgusted"))
        self.assertFalse(query_moodverse.get_mood("amazed"))
        self.assertFalse(query_moodverse.get_mood("clumsy"))

    def test_loading_invalid_moods_into_moodverse(self):
        bad_moods_loaded_from_json = {
            "rad":
                [""],  # lacks rad
            "good":
                [""],  # lacks good
            "neutral":
                [""],  # lacks neutral
            "bad":
                [""],  # lacks bad
            "awful":
                [""]  # lacks awful
        }

        with self.assertLogs(logging.getLogger(), level=logging.WARNING):
            Moodverse(bad_moods_loaded_from_json)

        bad_moods_loaded_from_json = {
            "rad":
                ["rad"],
            "good":
                ["good"],
            "neutral":
                ["neutral"],
            "bad":
                ["bed"],  # lacks bad
            "awful":
                [""]  # lacks awful
        }

        with self.assertLogs(logging.getLogger(), level=logging.WARNING):
            Moodverse(bad_moods_loaded_from_json)

        bad_moods_loaded_from_json = {
            "rad":
                ["rad"],
            "good":
                ["good"],
            "neutral":
                ["neutral"]
            # lacks bed
            # lacks awful
        }

        with self.assertLogs(logging.getLogger(), level=logging.WARNING):
            Moodverse(bad_moods_loaded_from_json)


class TestMoodGroup(TestCase):
    def test_create_group(self):
        self.assertRaises(ValueError, MoodGroup, "")
        self.assertTrue(MoodGroup("fancy"))

    def test_create_mood_in_this_group(self):
        my_fancy_group = MoodGroup("fancy")
        # Add two sample moods to this group
        my_fancy_group.create_mood()
        my_fancy_group.create_mood("out of this world")
        # And one wrong one
        with self.assertLogs(logging.getLogger(), logging.WARNING):
            my_fancy_group.create_mood("")

        # Check if they exist

        # checks __eq__ overload - obj(group_name) == str(group_name)
        self.assertEqual("fancy", my_fancy_group["fancy"])
        self.assertEqual("out of this world", my_fancy_group["out of this world"])

        # also checks __getitem__ - obj(group_name)[group_name]: List[mood: str]
        self.assertSetEqual({"out of this world", "fancy"}, set(my_fancy_group.known_moods))
