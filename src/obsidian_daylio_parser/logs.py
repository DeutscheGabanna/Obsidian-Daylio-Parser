from __future__ import annotations

import logging
import sys
from logging import LogRecord
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.traceback import install


class UniqueLogFilter:
    # copied directly from https://github.com/twizmwazin/unique_log_filter/blob/main/unique_log_filter.py
    # all credit goes to https://github.com/twizmwazin
    _logged: set[str]

    def __init__(self):
        self._logged = set()

    def filter(self, record: LogRecord):
        msg = record.getMessage()
        if msg in self._logged:
            return False
        self._logged.add(msg)
        return True


# makes uncaught exceptions handled by rich logging module
install(show_locals=True)


class LogMsg:
    """
    Used for common errors that will be logged by almost (if not all) loggers.
    Therefore, it is the base class of other Error child classes in specific files.
    It also provides a shorthand method for inserting variables into error messages - print().
    """
    # some common errors have been raised in scope into base class instead of child classes
    OBJECT_FOUND = "{}-class object found."
    OBJECT_NOT_FOUND = "{}-class object not found."
    FAULTY_OBJECT = "Called a {}-class object method but the object has been incorrectly instantiated."
    WRONG_VALUE = "Received {}, expected {}."

    @staticmethod
    def print(message: str, *args: str) -> Optional[str]:
        """
        Insert the args into an error message. If the error message expects n variables, provide n arguments.
        Returns a string with the already filled out message.
        """
        expected_args = message.count("{}")

        if len(args) != expected_args:
            logger.warning(
                f"Expected {expected_args} arguments for \"{message}\", but got {len(args)} instead."
            )
            return None
        return message.format(*args)


handler = RichHandler(
    level="WARNING",
    rich_tracebacks=True,
    markup=True
)
handler.addFilter(UniqueLogFilter())
# interesting discussion on why setLevel on both handler AND logger: https://stackoverflow.com/a/17668861/8527654
logging.basicConfig(level="DEBUG", handlers=[handler])
logger = logging.getLogger('rich')
