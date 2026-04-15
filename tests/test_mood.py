"""Unit tests for Moodverse — mood loading, lookup, and validation."""
import pytest

from obsidian_daylio_parser.entry.mood import Moodverse, MoodNotFoundError


class TestDefaultMoodverse:
    def test_has_no_custom_moods(self, default_moodverse):
        assert not default_moodverse.get_custom_moods

    @pytest.mark.parametrize("mood", ["rad", "good", "neutral", "bad", "awful"])
    def test_standard_moods_present(self, default_moodverse, mood):
        assert default_moodverse[mood] == mood

    def test_unknown_mood_raises(self, default_moodverse):
        with pytest.raises(MoodNotFoundError):
            default_moodverse["amazing"]

    def test_two_default_instances_are_equal(self):
        assert Moodverse() == Moodverse()

    def test_default_moods_dict(self, default_moodverse):
        assert default_moodverse.get_moods == {
            "rad": "rad", "good": "good", "neutral": "neutral", "bad": "bad", "awful": "awful"
        }


class TestCustomMoods:
    def test_valid_custom_moods_loaded(self):
        moods = {
            "rad": ["rad", "amazing"],
            "good": ["good", "nice"],
            "neutral": ["neutral", "ok", "fine"],
            "bad": ["bad"],
            "awful": ["awful", "miserable"],
        }
        mv = Moodverse(moods)
        # 5 non-duplicate customs: amazing, nice, ok, fine, miserable
        assert len(mv.get_custom_moods) == 5
        assert "nice" in mv.get_moods
        assert "amazing" in mv.get_moods
        assert "miserable" in mv.get_moods

    def test_unknown_group_keys_are_skipped(self):
        moods = {
            "holy cow": ["badger", "fox", "falcon"],
            "rad": ["amazing"],
            "good": ["nice"],
            "neutral": ["ok", "fine"],
            "bad": ["bad"],
            "awful": ["miserable"],
        }
        mv = Moodverse(moods)
        assert len(mv.get_custom_moods) == 5
        for animal in ("badger", "fox", "falcon"):
            with pytest.raises(MoodNotFoundError):
                mv[animal]

    def test_incomplete_moodlist_still_has_defaults(self):
        mv = Moodverse({"awful": ["miserable"]})
        assert mv.get_custom_moods
        assert "miserable" in mv.get_moods
        assert "good" in mv.get_moods

    @pytest.mark.parametrize(("moods", "expected_custom_count"), [
        ({"rad": ["", None], "good": [""], "neutral": ["", 15], "bad": ["", True], "awful": [""]}, 0),
        ({"rad": ["rad"], "good": ["good"], "neutral": ["neutral"], "bad": ["FALCON"], "awful": [""]}, 1),
        ({"rad": ["rad"], "good": ["good"], "neutral": ["neutral"], "bad": [None, 29, "badger"], "awful": [""]}, 1),
    ])
    def test_invalid_mood_values_skipped(self, moods, expected_custom_count):
        assert len(Moodverse(moods).get_custom_moods) == expected_custom_count


class TestMoodverseFromFile:
    def test_from_valid_json(self, custom_moodverse):
        assert custom_moodverse.get_custom_moods

    def test_from_none_gives_default(self):
        mv = Moodverse.from_file(None)
        assert not mv.get_custom_moods

    def test_from_invalid_file_gives_default(self, resources_path):
        mv = Moodverse.from_file(resources_path / "daylio_export_bad_empty.csv")
        assert not mv.get_custom_moods

    def test_incomplete_json_loads_partial_customs(self, resources_path):
        mv = Moodverse.from_file(resources_path / "moods_bad_missing_group.json")
        # incomplete.json has moods in rad, neutral, bad, awful but not good → 10 customs
        assert len(mv.get_custom_moods) == 10
