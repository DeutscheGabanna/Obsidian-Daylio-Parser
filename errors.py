import logging


# Formatter with fancy additions - colour and bold support - used in the console logger handler
class FancyFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # TODO: seems like format does not apply, only colouring works
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Common logging configuration for the root logger
# noinspection SpellCheckingInspection
logging.basicConfig(level=logging.DEBUG)

# Create a file handler for the root logger
file_log_handler = logging.FileHandler("debug.log")
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(FancyFormatter())

# Create a console handler for the root logger
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel(logging.WARNING)
console_log_handler.setFormatter(FancyFormatter())

# Add the handlers to the root logger
logging.getLogger().addHandler(file_log_handler)
logging.getLogger().addHandler(console_log_handler)


class ErrorMsgBase:
    """
    Used for common errors that will be logged by almost (if not all) loggers.
    Therefore, it is the base class of other Error child classes in specific files.
    It also provides a shorthand method for inserting variables into error messages - print().
    """
    # some common errors have been raised in scope into base class instead of child classes
    OBJECT_FOUND = "{}-class object found."
    OBJECT_NOT_FOUND = "{} object not found. Creating and returning to caller."
    FAULTY_OBJECT = "Called a {}-class object method but the object has been incorrectly instantiated."
    WRONG_VALUE = "Received {}, expected {}."

    @staticmethod
    def print(message: str, *args: str) -> str | None:
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
        else:
            return message.format(*args)
