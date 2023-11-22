import logging

# Common logging configuration for the root logger
# noinspection SpellCheckingInspection
msg_format = "(%(asctime)s) %(name)s [%(levelname)s]: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=msg_format)
formatter = logging.Formatter(msg_format)

# Create a file handler for the root logger
file_log_handler = logging.FileHandler("debug.log")
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(formatter)

# Create a console handler for the root logger
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel(logging.WARNING)
console_log_handler.setFormatter(formatter)

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
    def print(message, *args):
        """
        Insert the args into an error message. If the error message expects n variables, provide n arguments.
        Returns a string with the already filled out message.
        """
        return message.format(*args)
