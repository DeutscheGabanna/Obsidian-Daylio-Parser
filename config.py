"""
Sets up all necessary options and arguments.
.
├── Librarian/
│   ├── processing/
│   │   └── filepath
│   └── outputting/
│       ├── destination
│       └── force
|
├── DatedGroup/
│   ├── processing
│   └── outputting
|
└── DatedEntries/
    ├── processing/
    │   └── csv_delimiter
    └── outputting/
        ├── prefix
        ├── suffix
        ├── colour
        └── header
"""
import argparse
import logging
from typing import List

# Logging for config library
logger = logging.getLogger(__name__)


class SettingsManager:
    def __init__(self):
        # noinspection SpellCheckingInspection
        self.__console_arguments = argparse.ArgumentParser(
            fromfile_prefix_chars="@",
            prog="Daylio to Obsidian Parser",
            description="Converts Daylio .CSV backup file into Markdown files for Obsidian.",
            epilog="Created by DeutscheGabanna"
        )
        # regardless of whether you stick with these defaults or parse the console args, you get the same properties
        # useful for testing purposes when you do not want to invoke argparse
        # ---
        # Librarian
        # ---
        self.force = None
        # if you're wondering about these two below - I'd rather omit here positional arguments like these
        # it makes more sense for them to be passed as function arguments when initialising Librarian object
        #   self.filepath = "/_tests/sheet-1-valid-data.csv"
        #   self.destination = "/_tests/output_results/"
        # ---
        # Dated Entry
        # ---
        self.csv_delimiter = '|'
        self.header = 2
        self.tags = ["daily"]
        self.prefix = ''
        self.suffix = ''
        self.tag_activities = True
        self.colour = True

    def get_console(self):
        """
        Retrieves the :class:`argparse.ArgumentParser` object from :class:`SettingsManager` so you can modify it.
        :return: :class:`argparse.ArgumentParser`
        """
        return self.__console_arguments

    def parse_console(self):
        """
        Configures SettingsManager by accessing the console and retrieving the arguments used to run the script.
        """
        # namespace=self adds the properties to the SettingsManager obj, instead of creating a new Namespace obj
        # Without namespace=self
        # ---
        # - SettingsManager
        #   - Namespace obj that holds actual settings
        #       - foo = foo
        #       - bar = bar
        # With namespace=self
        # - SettingsManager
        #   - foo = foo
        #   - bar = bar
        self.__console_arguments.parse_args(namespace=self)

    def parse_spoofed_console(self, spoofed_string_of_args: List[str]):
        """
        Configures SettingsManager without accessing the console. Useful for testing purposes. Don't use it elsewhere.
        :param spoofed_string_of_args: Set of strs with positional and optional arguments as if written in CMD.
        """
        # namespace=self adds the properties to the SettingsManager obj, instead of creating a new Namespace obj
        # Without namespace=self
        # ---
        # - SettingsManager
        #   - Namespace obj that holds actual settings
        #       - foo = foo
        #       - bar = bar
        # With namespace=self
        # - SettingsManager
        #   - foo = foo
        #   - bar = bar
        self.__console_arguments.parse_args(args=spoofed_string_of_args, namespace=self)


# Global configuration
# ---
options = SettingsManager()

# Add some common options
options.get_console().add_argument(
    '--version',
    action='version',
    version='%(prog)s 3.0'
)

# TODO: User should be able to set verbosity level in logging
# TODO: Force-argument does nothing yet.
