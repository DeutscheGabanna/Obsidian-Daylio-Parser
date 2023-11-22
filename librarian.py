"""Provides a 2D array of mood groups and associated moods based on the moods.json file"""
import csv
import json
import logging
import sys

import config
import errors
import utils
from dated_entries_group import DatedEntriesGroup


class ErrorMsg(errors.ErrorMsgBase):
    FILE_INCOMPLETE = "{} is incomplete."
    FILE_EMPTY = "{} is empty."
    FILE_MISSING = "{} does not exist."
    PERMISSION_ERROR = "Cannot access {}."
    STANDARD_MOODS_USED = "Standard mood set (rad, good, neutral, bad, awful) will be used."
    DECODE_ERROR = "Error while decoding {}"
    NOT_A_FILE = "{} is not a file."
    CSV_ALL_FIELDS_PRESENT = "All expected columns are present in the CSV file columns."
    CSV_FIELDS_MISSING = "The following expected columns are missing: "
    COUNT_ROWS = "Found {} rows of data in {}."


standard_mood_set = {
    "rad": ["rad"],
    "good": ["good"],
    "neutral": ["neutral"],
    "bad": ["bad"],
    "awful": ["awful"]
}


class Librarian:
    def __init__(self,
                 path_to_file,
                 path_to_moods=None,
                 custom_config=config.get_defaults()):
        self.__known_moods = standard_mood_set
        self.__known_dates = {}
        self.__logger = logging.getLogger(self.__class__.__name__)

        self.__pass_file(path_to_file, custom_config)
        self.__set_custom_moods(path_to_moods)

    def has_custom_moods(self):
        return self.__known_moods != standard_mood_set

    def __set_custom_moods(self, json_file):
        """
        Overwrite the standard mood-set with a custom one.
        Mood-sets are used in output formatting to colour-code the dated entries.
        Mood-set is a dict with five keys: rad, good, neutral, bad and awful.
        Each key holds an array of any number of strings indicating various moods.
        """
        exp_path = utils.expand_path(json_file)
        try:
            with open(exp_path, encoding="UTF-8") as file:
                tmp_mood_set = json.load(file)
        except FileNotFoundError:
            self.__logger.warning(ErrorMsg.print(ErrorMsg.FILE_MISSING, exp_path))
            return False
        except PermissionError:
            self.__logger.warning(ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, exp_path))
            return False
        except json.JSONDecodeError:
            self.__logger.warning(ErrorMsg.print(ErrorMsg.DECODE_ERROR, exp_path))
            return False

        # Try accessing each mood key to raise KeyError if missing
        for mood_key in self.__known_moods.keys():
            try:
                tmp_mood_set[mood_key]
            except KeyError:
                self.__logger.warning(ErrorMsg.print(ErrorMsg.FILE_INCOMPLETE, exp_path))
                return False
            else:
                continue

        # At this point, we know each mood key is present so the dictionary is valid
        self.__known_moods = tmp_mood_set
        return True

    def __pass_file(self, filepath, custom_config):
        """
        Open and parse filepath. Then structure it into Date & DatedEntry objects.
        """
        if not self.has_custom_moods():
            self.__logger.info(ErrorMsg.print(ErrorMsg.STANDARD_MOODS_USED))

        try:
            file = open(filepath, newline='', encoding='UTF-8')
        except FileNotFoundError:
            self.__logger.critical(ErrorMsg.print(ErrorMsg.FILE_MISSING, filepath))
            sys.exit(1)  # no point in continuing
        except PermissionError:
            self.__logger.critical(ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, filepath))
            sys.exit(1)  # no point in continuing
        except OSError:
            self.__logger.critical(OSError)
            sys.exit(1)  # no point in continuing

        expected_fields = [
            "full_date",
            "date",
            "weekday",
            "time",
            "mood",
            "activities",
            "note",
            "note_title",
            "note"
        ]

        with file:
            # Is it a valid CSV?
            try:
                # strict parameter throws csv.Error if parsing fails
                raw_lines = csv.DictReader(file, delimiter=',', quotechar='"', strict=True)
            except csv.Error:
                self.__logger.critical(ErrorMsg.print(ErrorMsg.DECODE_ERROR, filepath))
                sys.exit(1)

            # Does it have all the fields?
            missing_strings = [expected_field for expected_field in expected_fields if
                               expected_field not in raw_lines.fieldnames]
            if not missing_strings:
                self.__logger.debug(ErrorMsg.print(ErrorMsg.CSV_ALL_FIELDS_PRESENT))
            else:
                self.__logger.critical(
                    ErrorMsg.print(
                        ErrorMsg.CSV_FIELDS_MISSING,
                        {', '.join(missing_strings)}
                    )
                )
                sys.exit(1)

            # Does it have any rows besides the header?
            try:
                next(raw_lines)
            except StopIteration:
                self.__logger.critical(ErrorMsg.print(ErrorMsg.FILE_EMPTY, filepath))
                sys.exit(1)

            # Do any of the rows lack required fields?
            lines_parsed = 0
            for line in raw_lines:
                line: dict[str]     # fix parser incorrectly assuming type
                if len(line) < 7:
                    self.__logger.warning(ErrorMsg.print(ErrorMsg.FILE_INCOMPLETE, line))
                else:
                    entry = self.access_date(line["full_date"]).access_dated_entry(line["time"])
                    entry.set_mood(line["mood"], self.__known_moods)
                    entry.set_activities(line["activities"], custom_config.csv_delimiter, custom_config.tag_activities)
                    entry.set_title(line["note_title"])
                    entry.set_note(line["note"])
                    lines_parsed += 1
            self.__logger.info(ErrorMsg.print(ErrorMsg.COUNT_ROWS, lines_parsed, filepath))

        return self

    def access_date(self, target_date):
        date_obj = DatedEntriesGroup(target_date)

        # have you already filed this date?
        if target_date in self.__known_dates:
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_FOUND, target_date))
        else:
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_NOT_FOUND, target_date))
            self.__known_dates[date_obj.get_uid()] = date_obj

        return date_obj
