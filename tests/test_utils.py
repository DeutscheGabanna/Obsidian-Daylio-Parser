"""Unit tests for obsidian_daylio_parser.utils — pure functions, no I/O beyond fixture files."""
import datetime
import logging

import pytest

from obsidian_daylio_parser import utils, logs


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------
class TestSlugify:
    @pytest.mark.parametrize("text, expected", [
        ("ConvertThis to-------a SLUG", "convertthis-to-a-slug"),
        ("Zażółć gęślą jaźń    ", "zażółć-gęślą-jaźń"),
        ("  Multiple   spaces  between    words", "multiple-spaces-between-words"),
        ("Хлеба нашего повшеднего", "хлеба-нашего-повшеднего"),
    ])
    def test_slugify_no_tag(self, text, expected):
        assert utils.slugify(text, taggify=False) == expected

    def test_slugify_warns_on_leading_digit(self, caplog):
        with caplog.at_level(logging.WARNING, logger="obsidian_daylio_parser.utils"):
            utils.slugify("1. Digit cannot appear at the beginning of a tag", taggify=True)
        assert any("invalid" in r.message.lower() for r in caplog.records)

    def test_slugify_no_warning_on_mid_or_trailing_digits(self, caplog):
        with caplog.at_level(logging.WARNING, logger="obsidian_daylio_parser.utils"):
            utils.slugify("Digits within the string 1234 - are ok", taggify=True)
            utils.slugify("Digits at the end of the string are also ok 456", taggify=True)
        assert not caplog.records


# ---------------------------------------------------------------------------
# expand_path
# ---------------------------------------------------------------------------
class TestExpandPath:
    def test_expands_home_directory(self):
        assert not utils.expand_path("~/yes").startswith("~")

    def test_expands_env_vars(self):
        assert not utils.expand_path("$HOME/whatever").startswith("$HOME")


# ---------------------------------------------------------------------------
# strip_and_get_truthy / slice_quotes
# ---------------------------------------------------------------------------
class TestStripping:
    def test_strip_and_get_truthy(self):
        assert utils.strip_and_get_truthy('"one||two|||||"', "|") == ["one", "two"]
        assert utils.strip_and_get_truthy('""', "|") == []

    def test_slice_quotes(self):
        assert utils.slice_quotes('"test"') == "test"
        assert utils.slice_quotes('""') is None
        assert utils.slice_quotes('" bicycle   "') == "bicycle"


# ---------------------------------------------------------------------------
# IO context managers
# ---------------------------------------------------------------------------
class TestIOContextManagers:
    def test_json_loader(self, fixtures_path):
        expected = {"rad": ["rad"], "good": ["good"], "neutral": ["okay"], "bad": ["bad"], "awful": ["awful"]}
        with utils.JsonLoader().load(str(fixtures_path / "moods" / "smallest.json")) as data:
            assert data == expected

    def test_csv_loader(self, fixtures_path):
        with utils.CsvLoader().load(str(fixtures_path / "all-valid.csv")) as reader:
            first_row = next(reader)
        assert first_row["full_date"] == "2022-10-30"
        assert first_row["mood"] == "vaguely ok"


# ---------------------------------------------------------------------------
# guess_time_type
# ---------------------------------------------------------------------------
class TestGuessTimeType:
    @pytest.mark.parametrize("raw, expected", [
        ("02:30 PM", datetime.time(14, 30)),
        ("12:00 AM", datetime.time(0, 0)),
        ("12:00 PM", datetime.time(12, 0)),
        ("14:30", datetime.time(14, 30)),
        ("00:00", datetime.time(0, 0)),
        ("23:59", datetime.time(23, 59)),
        ("2:30 PM", datetime.time(14, 30)),
        ("2:30", datetime.time(2, 30)),
        ("11:59 PM", datetime.time(23, 59)),
        ("12:01 AM", datetime.time(0, 1)),
        ("2:30PM", datetime.time(14, 30)),
        ("2:30 pm", datetime.time(14, 30)),
        ("02:30pm", datetime.time(14, 30)),
        ("  14:30  ", datetime.time(14, 30)),
        ("2:30 PM  ", datetime.time(14, 30)),
    ])
    def test_valid_strings(self, raw, expected):
        assert utils.guess_time_type(raw) == expected

    @pytest.mark.parametrize("raw, expected", [
        ([14, 30], datetime.time(14, 30)),
        ([0, 0], datetime.time(0, 0)),
        ([23, 59], datetime.time(23, 59)),
    ])
    def test_valid_lists(self, raw, expected):
        assert utils.guess_time_type(raw) == expected

    def test_time_object_passthrough(self):
        t = datetime.time(14, 30)
        assert utils.guess_time_type(t) == t

    @pytest.mark.parametrize("raw", [
        "25:00", "14:60", "2:30 ZM", "not a time", "12:", ":30",
    ])
    def test_invalid_strings(self, raw):
        with pytest.raises(utils.InvalidTimeError):
            utils.guess_time_type(raw)

    @pytest.mark.parametrize("raw", [
        [14, 30, 0], [14],
    ])
    def test_invalid_lists(self, raw):
        with pytest.raises(utils.InvalidTimeError):
            utils.guess_time_type(raw)


# ---------------------------------------------------------------------------
# guess_date_type
# ---------------------------------------------------------------------------
class TestGuessDateType:
    @pytest.mark.parametrize("raw, expected", [
        ("2023-05-15", datetime.date(2023, 5, 15)),
        ("2000-01-01", datetime.date(2000, 1, 1)),
        ("2099-12-31", datetime.date(2099, 12, 31)),
        ("2023-5-15", datetime.date(2023, 5, 15)),
        ("  2023-05-15  ", datetime.date(2023, 5, 15)),
        ("2024-02-29", datetime.date(2024, 2, 29)),  # leap year
        ("9999-12-31", datetime.date(9999, 12, 31)),
    ])
    def test_valid_strings(self, raw, expected):
        assert utils.guess_date_type(raw) == expected

    @pytest.mark.parametrize("raw, expected", [
        ([2023, 5, 15], datetime.date(2023, 5, 15)),
        ([2000, 1, 1], datetime.date(2000, 1, 1)),
        (["2023", "05", "15"], datetime.date(2023, 5, 15)),
        (["2023", 5, "15"], datetime.date(2023, 5, 15)),
        ([1, 1, 1], datetime.date(1, 1, 1)),
    ])
    def test_valid_lists(self, raw, expected):
        assert utils.guess_date_type(raw) == expected

    def test_date_object_passthrough(self):
        d = datetime.date(2023, 5, 15)
        assert utils.guess_date_type(d) == d

    @pytest.mark.parametrize("raw", [
        "2023/05/15", "15-05-2023",
        [2023, 5], [2023, 5, 15, 12], [2023, 13, 1], [2023, 2, 30],
    ])
    def test_invalid_inputs(self, raw):
        with pytest.raises(utils.InvalidDateError):
            utils.guess_date_type(raw)

    @pytest.mark.parametrize("raw", [20230515, {"year": 2023, "month": 5, "day": 15}])
    def test_wrong_types(self, raw):
        with pytest.raises(utils.InvalidDateError):
            utils.guess_date_type(raw)


# ---------------------------------------------------------------------------
# LogMsg.print (migrated from test_errors.py)
# ---------------------------------------------------------------------------
class TestLogMsg:
    def test_print_with_correct_args(self):
        result = logs.LogMsg.print(logs.LogMsg.WRONG_VALUE, "x", "y")
        assert isinstance(result, str)

    def test_print_with_missing_arg(self):
        assert logs.LogMsg.print(logs.LogMsg.WRONG_VALUE, "y") is None
