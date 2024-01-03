"""
Contains universally useful functions
"""
import re
import os
import logging
import errors


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_OBSIDIAN_TAGS = "You want your activities as tags, but {} is invalid."


class Core:
    def __init__(self):
        self.__uid = None

    def __bool__(self):
        return self.__uid is not None

    def __str__(self):
        return str(self.__uid)

    # TODO: These are supposed to be pythonic setters, not this imitation
    def set_uid(self, value):
        self.__uid = value

    def get_uid(self):
        return str(self.__uid)


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
    # Converts the filepath to an absolute path and then expands the tilde (~) character to the user's home directory
    return os.path.expanduser(
        # Expands environment variables in the path, such as %appdata%
        os.path.expandvars(path)
    )
