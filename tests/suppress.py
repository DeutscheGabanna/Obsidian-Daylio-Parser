import contextlib
import logging
import os


class DisableLogging:
    def __init__(self, logger_name: str = None):
        self.logger = logging.getLogger(logger_name)
        self.original_level = self.logger.getEffectiveLevel()

    def __enter__(self):
        self.logger.setLevel(logging.CRITICAL + 1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


def out(func):
    def wrapper(*a, **ka):
        with open(os.devnull, 'w') as devnull, \
                contextlib.redirect_stdout(devnull), \
                contextlib.redirect_stderr(devnull), \
                DisableLogging():
            return func(*a, **ka)

    return wrapper
