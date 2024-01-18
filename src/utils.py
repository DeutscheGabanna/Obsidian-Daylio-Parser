"""
Contains universally useful functions
"""
import logging
import os
import re

from src import errors


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


def slugify(text: str, taggify: bool):
    # noinspection SpellCheckingInspection
    """
    Simple slugification function to transform text. Works on non-latin characters too.
    """
    logger = logging.getLogger(__name__)
    text = str(text).lower()
    text = re.sub(re.compile(r"\s+"), '-', text)  # Replace spaces with -
    text = re.sub(re.compile(r"[^\w\-]+"), '', text)  # Remove all non-word chars
    text = re.sub(re.compile(r"--+"), '-', text)  # Replace multiple - with single -
    text = re.sub(re.compile(r"^-+"), '', text)  # Trim - from start of text
    text = re.sub(re.compile(r"-+$"), '', text)  # Trim - from end of text
    if taggify:
        if re.match('[0-9]', text):
            logger.warning(ErrorMsg.print(ErrorMsg.INVALID_OBSIDIAN_TAGS, text))
    return text


def expand_path(path):
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
