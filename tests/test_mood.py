import pytest

from daylio_to_md.entry.mood import Moodverse, MoodNotFoundError


class TestMoodverse:

    def test_default_moodverse_no_customisation(self):
        moodverse = Moodverse()

        assert not moodverse.get_custom_moods
        assert moodverse["rad"] == "rad"
        assert moodverse["bad"] == "bad"

        with pytest.raises(MoodNotFoundError):
            moodverse["amazing"]

        # don't compare Moodverses by their memory address, but by their contents
        assert Moodverse() == Moodverse()

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

        assert my_moodverse.get_moods != {
            "rad": "rad", "good": "good", "neutral": "neutral", "bad": "bad", "awful": "awful"
        }
        # in total there are 10 moods, but there are only 5 additional moods if you skip duplicates from defaults
        assert len(my_moodverse.get_custom_moods) == 5
        assert "nice" in my_moodverse.get_moods
        assert "amazing" in my_moodverse.get_moods
        assert "miserable" in my_moodverse.get_moods

        default_moodverse = Moodverse()
        assert "neutral" in default_moodverse.get_moods
        assert "bad" in default_moodverse.get_moods
        assert "awful" in default_moodverse.get_moods
        assert "good" in default_moodverse.get_moods
        assert "rad" in default_moodverse.get_moods

        with pytest.raises(MoodNotFoundError):
            default_moodverse["terrific"]

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
        assert len(my_moodverse.get_custom_moods) == 5, f"Custom moods: {my_moodverse.get_custom_moods.keys()}"

        # Standard moods should still be in the groups, irrespective of what was in the custom dictionary
        assert "rad" in my_moodverse.get_moods
        assert "good" in my_moodverse.get_moods
        assert "awful" in my_moodverse.get_moods
        assert "neutral" in my_moodverse.get_moods

        with pytest.raises(MoodNotFoundError):
            my_moodverse["badger"]
        with pytest.raises(MoodNotFoundError):
            my_moodverse["fox"]
        with pytest.raises(MoodNotFoundError):
            my_moodverse["falcon"]

    def test_loading_incomplete_moodlists(self):
        moodlist_incomplete = {
            "awful": ["miserable"]
        }

        my_moodverse = Moodverse(moodlist_incomplete)

        assert len(my_moodverse.get_custom_moods) > 0
        assert "miserable" in my_moodverse.get_moods
        assert "awful" in my_moodverse.get_moods
        assert "good" in my_moodverse.get_moods

    def test_loading_invalid_moodlists(self):
        bad_moods_loaded_from_json = {
            "rad": ["", None],
            "good": [""],
            "neutral": ["", 15],
            "bad": ["", True],
            "awful": [""]
        }
        assert len(Moodverse(bad_moods_loaded_from_json).get_custom_moods) == 0

        bad_moods_loaded_from_json = {
            "rad": ["rad"],
            "good": ["good"],
            "neutral": ["neutral"],
            "bad": ["bed"],
            "awful": [""]  # <--
        }
        assert len(Moodverse(bad_moods_loaded_from_json).get_custom_moods) == 1

    def test_loading_same_moods_as_already_existing(self):
        expected_moods = {
            "rad": "rad",
            "good": "good",
            "neutral": "neutral",
            "bad": "bad",
            "awful": "awful"
        }
        assert Moodverse().get_moods == expected_moods


# Parametrized tests for cleaner exception testing
class TestMoodverseExceptions:

    @pytest.mark.parametrize("invalid_mood", ["amazing", "terrific", "badger", "fox", "falcon"])
    def test_default_moodverse_raises_on_unknown_moods(self, invalid_mood):
        with pytest.raises(MoodNotFoundError):
            Moodverse()[invalid_mood]


# Fixtures for common test data
@pytest.fixture
def valid_custom_moods():
    return {
        "rad": ["rad", "amazing"],
        "good": ["good", "nice"],
        "neutral": ["neutral", "ok", "fine"],
        "bad": ["bad"],
        "awful": ["awful", "miserable"]
    }


@pytest.fixture
def moodverse_with_custom_moods(valid_custom_moods):
    return Moodverse(valid_custom_moods)


# Example of using fixtures
class TestMoodverseWithFixtures:

    def test_custom_moods_count(self, moodverse_with_custom_moods):
        assert len(moodverse_with_custom_moods.get_custom_moods) == 5

    def test_custom_moods_accessible(self, moodverse_with_custom_moods):
        assert "amazing" in moodverse_with_custom_moods.get_moods
        assert "nice" in moodverse_with_custom_moods.get_moods
        assert "miserable" in moodverse_with_custom_moods.get_moods