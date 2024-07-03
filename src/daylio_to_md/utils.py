"""
Contains universally useful functions
"""
import logging
import os
import re
from typing import List

from daylio_to_md import errors


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_OBSIDIAN_TAGS = "You want your activities as tags, but {} is invalid."


class Core:
    def __init__(self, uid):
        self.__uid = uid

    def __bool__(self):
        return self.__uid is not None

    def __str__(self):
        return str(self.__uid)

    def __hash__(self):
        return hash(self.uid)

    @property
    def uid(self):
        return self.__uid


class CustomException(Exception):
    def __init__(self, message=None):
        super().__init__(message)
        self.message = message


class StreamError(CustomException):
    pass


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


def slice_quotes(string: str) -> str | None:
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
