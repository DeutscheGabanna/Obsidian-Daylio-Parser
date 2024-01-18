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

    def emit(self, record):
        # We don't use white for any logging, to help distinguish from user print statements
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


# Create a console handler for the root logger
# noinspection SpellCheckingInspection
console_log_handler = ColorHandler(sys.stdout)
console_log_handler.setLevel(logging.DEBUG)

# noinspection SpellCheckingInspection
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)")
console_log_handler.setFormatter(formatter)

# Add the handlers to the root logger
logging.getLogger().addHandler(console_log_handler)


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
