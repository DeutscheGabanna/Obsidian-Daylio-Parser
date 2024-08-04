import logging
import sys
from typing import Optional


class ColorHandler(logging.StreamHandler):
    # https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    GRAY8 = "38;5;8"
    GRAY7 = "38;5;7"
    ORANGE = "33"
    RED = "31"
    WHITE = "0"

    # noinspection PyPep8
    def emit(self, record):
        # We don't use white for any logging, to help distinguish from user print statements
        # noinspection PyPep8
        level_color_map = {
            logging.DEBUG: self.GRAY8,
            logging.INFO: self.GRAY7,
            logging.WARNING: self.ORANGE,
            logging.ERROR: self.RED,
            logging.CRITICAL: f"1;{self.RED}",  # Bold for critical errors
        }

        csi = f"{chr(27)}["  # control sequence introducer
        color = level_color_map.get(record.levelno, self.WHITE)

        # Apply the formatter to format the log message
        formatted_msg = self.format(record)

        self.stream.write(f"{csi}{color}m{formatted_msg}{csi}m\n")


class DuplicateFilter(logging.Filter):
    # Class-level attribute to store logged messages
    logged_messages = set()

    def filter(self, record):
        # Create a unique identifier for the log message
        current_log = (record.module, record.levelno, record.msg)

        if current_log in DuplicateFilter.logged_messages:
            return False  # Filter out the message if it's a duplicate

        DuplicateFilter.logged_messages.add(current_log)
        return True  # Allow the log through if it's not a duplicate


# Create a console handler for the root logger
# noinspection SpellCheckingInspection
console_log_handler = ColorHandler(sys.stdout)
console_log_handler.addFilter(DuplicateFilter())
# interesting discussion on why setLevel on both handler AND logger: https://stackoverflow.com/a/17668861/8527654

console_log_handler.setLevel(logging.INFO)
# noinspection SpellCheckingInspection
formatter = logging.Formatter("%(name)s\t%(levelname)s\t%(message)s")

console_log_handler.setFormatter(formatter)
# Add the handlers to the root logger
logging.getLogger().addHandler(console_log_handler)
logging.getLogger().setLevel(logging.INFO)


class ErrorMsgBase:
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
            logging.getLogger(__name__).warning(
                f"Expected {expected_args} arguments for \"{message}\", but got {len(args)} instead."
            )
            return None
        return message.format(*args)
