"""
Contains universally useful functions
"""
from __future__ import annotations

import abc
import csv
import dataclasses
import datetime
import json
import logging
import os
import re
import typing
from contextlib import contextmanager
from typing import List, TextIO, Optional, Union

from daylio_to_md import errors

EXPECTED_FIELDS = frozenset([
   "full_date",
   "date",
   "weekday",
   "time",
   "mood",
   "activities",
   "note",
   "note_title"
])

"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""
CSV_ALL_FIELDS_PRESENT = "All expected columns are present in the CSV file columns, namely: {}."
CSV_FIELDS_MISSING = "The following expected columns are missing: {}"


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_OBSIDIAN_TAGS = "You want your activities as frontmatter_tags, but {} is invalid."


class ExpectedValueError(TypeError):
    """Expected {}, got {} instead."""

    def __init__(self, expected_value, actual_value):
        super().__init__()
        self.__expected_value = expected_value
        self.__actual_value = actual_value
        try:
            self.__doc__ = self.__doc__.format(expected_value, actual_value)
        except KeyError:
            pass

    @property
    def expected_value(self):
        return self.__expected_value

    @property
    def actual_value(self):
        return self.__actual_value


# It is open to interpretation whether an invalid date is more of a TypeError or ValueError Exception
class InvalidDateError(ExpectedValueError, ValueError):
    """String {} is not a valid date. Check :class:`datetime.Date` for details."""

    def __init__(self, date_passed):
        super().__init__(datetime.date.__class__.__name__, str(date_passed))


class InvalidTimeError(ExpectedValueError):
    """String {} is not a valid date. Check :class:`datetime.Time` for details."""

    def __init__(self, time_passed):
        super().__init__(datetime.time.__class__.__name__, str(time_passed))


class CouldNotLoadFileError(Exception):
    """The file {} could not be accessed."""

    def __init__(self, path):
        super().__init__()
        self.__path = str(path)
        self.__doc__ = self.__doc__.format(self.__path)

    @property
    def path(self):
        return self.__path


class InvalidDataInFileError(ExpectedValueError):
    """
    The file does not follow the expected structure.
    Fieldnames expected: {}
    Fieldnames received: {}
    """

    def __init__(self, expected_fieldnames, actual_fieldnames):
        super().__init__(expected_fieldnames, actual_fieldnames)


class IncompleteDataRow(InvalidDataInFileError):
    """
    While the file appeared to follow expected structure in fieldnames, this particular row does not have enough cells.
    Expected cells: {}
    Received cells: {}
    """

    def __init__(self, expected_fields, actual_fields):
        super().__init__(expected_fields, actual_fields)


class TooManyCellsInRowError(InvalidDataInFileError):
    """
    While the file appeared to follow expected structure in fieldnames, this particular row has too many cells.
    Expected cells: {}
    Received cells: {}
    """

    def __init__(self, expected_fields, actual_fields):
        super().__init__(expected_fields, actual_fields)


class StreamError(Exception):
    pass


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


class Core:
    def __init__(self, uid):
        self.__uid = uid

    def __bool__(self):
        return self.__uid is not None

    def __str__(self):
        return str(self.__uid)

    def __hash__(self):
        return hash(self.uid)

    def __repr__(self):
        return "{object}({uid})".format(object=self.__class__.__name__, uid=self.uid)

    @property
    def uid(self):
        return self.__uid


def slugify(text: str, taggify: bool) -> str:
    # noinspection SpellCheckingInspection
    """
    Simple slugification function to transform text. Works on non-latin characters too.
    """
    logger = logging.getLogger(__name__)
    text = str(text).lower().strip()  # get rid of trailing spaces left after splitting activities apart from one string
    text = re.sub(re.compile(r"\s+"), '-', text)  # Replace spaces with -
    text = re.sub(re.compile(r"[^\w\-]+"), '', text)  # Remove all non-word chars
    text = re.sub(re.compile(r"--+"), '-', text)  # Replace multiple - with single -
    text = re.sub(re.compile(r"^-+"), '', text)  # Trim - from start of text
    text = re.sub(re.compile(r"-+$"), '', text)  # Trim - from end of text
    # Checks if the tag is actually a valid tag in Obsidian - still appends the hash even if not, but warns at least
    if taggify:
        if re.match('[0-9]', text):
            logger.warning(ErrorMsg.print(ErrorMsg.INVALID_OBSIDIAN_TAGS, text))
    return '#' + text if taggify else text


def expand_path(path: str) -> str:
    """
    Expand all %variables%, ~/home-directories and relative parts in the path. Return the expanded path.
    It does not use os.path.abspath() because it treats current script directory as root.
    """
    # Gets full path, resolving things like ../
    return os.path.realpath(
        # Expands the tilde (~) character to the user's home directory
        os.path.expanduser(
            os.path.expandvars(path)
        )
    )


def slice_quotes(string: str) -> Optional[str]:
    """
    Gets rid of initial and terminating quotation marks inserted by Daylio
    :param string: string to be sliced
    :returns: string without quotation marks in the beginning and end of the initial string, or nothing if "" provided.
    """
    # only 2 characters? Then it is an empty cell, because Daylio wraps its values inside "" like so: "","","",""...
    return string.strip("\"").strip() if string and len(string) > 2 else None


def strip_and_get_truthy(delimited_string: str, delimiter: str) -> List[str]:
    """
    Pipe delimited strings may result in arrays that contain zero-length strings.
    While such strings in itself are falsy, any array that has them is automatically truthy, unfortunately.
    Therefore, I use list comprehension to discard such falsy values from an array and return the sanitised array.
    :returns: array without falsy values, even if it results in empty (falsy) array
    """
    # I need to separate returning into the guard statement and actual return because slice_quotes can produce null vals
    if delimited_string is None:
        return []

    sliced_del_string = slice_quotes(delimited_string)

    return [el for el in sliced_del_string.split(delimiter) if el] if sliced_del_string else []


class FileLoader:
    # all subclasses of FileLoader need to implement this method one way or the other
    # basically an interface requirement
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)

    @property
    def logger(self):
        return self.__logger

    @abc.abstractmethod
    def _load_file(self, file: TextIO):
        pass

    @contextmanager
    def load(self, path: str) -> typing.Any:
        """
        Loads the file into context manager and catches exceptions thrown while doing so.
        It catches errors specific to the implementation first, then tries to catch more general IO errors.
        :return: It is not specified what kind of object will be returned when opened. Left up to implementation.
        """
        try:
            with open(expand_path(path), encoding='UTF-8') as file:
                yield self._load_file(file)
        # TypeError is thrown when a None argument is passed
        except (FileNotFoundError, PermissionError, OSError, UnicodeDecodeError, TypeError) as err:
            raise CouldNotLoadFileError(path) from err


class JsonLoader(FileLoader):
    def __init__(self):
        super().__init__()

    def _load_file(self, file: TextIO):
        try:
            return json.load(file)
        # JSON specific errors
        except json.JSONDecodeError as err:
            raise CouldNotLoadFileError from err


class CsvLoader(FileLoader):
    """
    :raises CouldNotLoadFileError: if file cannot be opened or processed
    """
    def __init__(self, expected_fields: frozenset[str] = EXPECTED_FIELDS):
        super().__init__()
        self.__expected_fields = expected_fields

    def _load_file(self, file: TextIO):
        try:
            # strict parameter throws csv.Error if parsing fails
            loaded_csv = csv.DictReader(file, delimiter=',', quotechar='"', strict=True)
            self.validate_fieldnames(loaded_csv.fieldnames, self.__expected_fields)
            return loaded_csv
        # CSV specific errors
        except (csv.Error, InvalidDataInFileError) as err:
            raise CouldNotLoadFileError from err

    def validate_fieldnames(self, fieldnames, expected_fields) -> set[str]:
        # Does it have all the fields? Push any missing field into an array for later reference
        # Even if only one column from the list below is missing in the CSV, it's a problem while parsing later
        # Let's have a look at what columns we have in the parsed CSV
        missing_strings = {
            expected_field for expected_field in expected_fields if
            expected_field not in fieldnames
        }
        if len(missing_strings) > 0:
            self.__logger.critical(CSV_FIELDS_MISSING.format(', '.join(missing_strings)))
            raise InvalidDataInFileError(expected_fields, fieldnames)

        self.logger.debug(CSV_ALL_FIELDS_PRESENT.format(', '.join(missing_strings)))
        return missing_strings


# Optional[str] as key means either str or None. None can be a key and this case is explained below
# noinspection PyTypeChecker
def validate_line(line: dict[Optional[str], str]) -> dict[str, Union[str, datetime.date, datetime.time]]:
    """
    Checks
    ------
    If there are exactly as many cells as expected fields, even if some of them are empty (i.e. only commas)

    Expected fields
    ---------------
    - "full_date",
    - "date",
    - "weekday",
    - "time",
    - "mood",
    - "activities",
    - "note",
    - "note_title"

    :param line: a dictionary with values from the currently processed CSV line
    :raises TooManyCellsInRowError: if there are too many cells in a row
    :raises IncompleteDataRow: if there are too few cells in a row
    :raises InvalidDateError: if the date in the full_date cell is invalid
    :returns: the same line, but...
        - the value of date changed from :class:`str` to :class:`datetime.date`
        - the value of time changed from :class:`str` to :class:`datetime.time`
    """
    # noinspection SpellCheckingInspection
    # Does it have more cells than there are expected fields?
    # from https://docs.python.org/3/library/csv.html#csv.DictReader
    # If a row has more fields than fieldnames, the remaining data is put in a list and stored with the field name
    # specified by restkey (which defaults to None). If a non-blank row has fewer fields than fieldnames,
    # the missing values are filled-in with the value of restval (which defaults to None).
    if None in line:
        raise TooManyCellsInRowError(EXPECTED_FIELDS, line.keys())

    # Even if it does not have actual values for all expected fields, does it at least have enough commas?
    if len(line) < len(EXPECTED_FIELDS):
        raise IncompleteDataRow(EXPECTED_FIELDS, line.keys())

    # Good to go, at least for now
    # The line could still be faulty, but any faults can now only be detected by Entry object
    return line


"""---------------------------------------------------------------------------------------------------------------------
DATE AND TIME
---------------------------------------------------------------------------------------------------------------------"""


def guess_date_type(this: typing.Union[datetime.date, str, typing.List[str], typing.List[int]]) -> datetime.date:
    """
    Supported formats
    -----------------
    - "%Y-%m-%d"   - ISO 8601 format
    - "%d/%m/%Y"   - Day/Month/Year format
    - "%m/%d/%Y"   - Month/Day/Year format
    - "%B %d, %Y"  - Month name, day, year
    - "%d %B %Y"   - Day, month name, year
    - "%Y%m%d"     - Basic ISO format (no separators)

    Examples
    --------
    - "%Y-%m-%d"   -> "2023-05-15"
    - "%d/%m/%Y"   -> "15/05/2023"
    - "%m/%d/%Y"   -> "05/15/2023"
    - "%B %d, %Y"  -> "May 15, 2023"
    - "%d %B %Y"   -> "15 May 2023"
    - "%Y%m%d"     -> "20230515"

    :param this: date to be coerced into :class:`datetime.date` object. Strips leading and trailing spaces if a string.
    :raise InvalidDateError: if it cannot be coerced into proper object type
    :return: :class:`datetime.date` object
    """
    proper_date_obj: datetime.date

    if isinstance(this, str):
        this = this.strip()
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%d %B %Y", "%Y%m%d"]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(this, fmt).date()
            except ValueError:
                continue
        raise InvalidDateError(this)
    elif isinstance(this, typing.List) and len(this) == 3:
        year, month, day = (int(el) for el in this)
        try:
            proper_date_obj = datetime.date(year, month, day)
        except ValueError as err:
            raise InvalidDateError(this) from err
    elif isinstance(this, datetime.date):
        proper_date_obj = this
    else:
        raise InvalidDateError(this)

    return proper_date_obj


def guess_time_type(this: typing.Union[datetime.time, str, typing.List[str], typing.List[int]]) -> datetime.time:
    """
    Supported formats
    ------------------
        - "%I:%M %p"  - 12-hour format with AM/PM
        - "%I:%M%p"  - 12-hour format with AM/PM but without a space as a delimiter
        - "%H:%M"     - 24-hour format
        - "%-I:%M %p" - 12-hour format with AM/PM, no leading zero for hour
        - "%-H:%M"    - 24-hour format, no leading zero for hour

    Examples
    --------
        - "%I:%M %p"  -> "01:30 PM", "12:45 AM"
        - "%I:%M%p"   -> "11:45PM", "03:55AM"
        - "%H:%M"     -> "13:30", "00:45"
        - "%-I:%M %p" -> "1:30 PM", "12:45 AM"
        - "%-I:%M%p"  -> "10:00PM", "6:10AM"
        - "%-H:%M"    -> "13:30", "0:45"

    :param this: time to be coerced into :class:`datetime.time` object. Strips leading and trailing spaces if a string.
    :raise InvalidTimeError: if ``this`` cannot be coerced into proper object type
    :return: :class:`datetime.time` object
    """
    proper_time_obj: datetime.time

    if isinstance(this, str):
        formats = ["%I:%M %p", "%I:%M%p", "%H:%M", "%-I:%M %p", "%-I:%M%p", "%-H:%M"]
        for fmt in formats:
            try:
                # https://stackoverflow.com/questions/3183707/stripping-off-the-seconds-in-datetime-python
                proper_time_obj = datetime.datetime.strptime(this.strip(), fmt).time()
                break
            except ValueError:
                continue
        else:
            raise InvalidTimeError(this)
    elif isinstance(this, typing.List) and len(this) == 2:
        hours, minutes = (int(el) for el in this)
        try:
            proper_time_obj = datetime.time(hours, minutes)
        except ValueError as err:
            raise InvalidTimeError(this) from err
    elif isinstance(this, datetime.time):
        proper_time_obj = this
    else:
        raise InvalidTimeError(this)

    return proper_time_obj.replace(second=0, microsecond=0)


def ensure_dir(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
