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
from typing import List, Any

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
        self.filepath = None
        self.destination = None
        # TODO: Force-argument does nothing yet.
        self.force = None
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
        # TODO: User should be able to set verbosity level in logging

    @property
    def arg_console(self) -> argparse.ArgumentParser:
        """
        Retrieves the :class:`argparse.ArgumentParser` object from :class:`SettingsManager` so you can modify it.
        :return: :class:`argparse.ArgumentParser`
        """
        return self.__console_arguments

    def parse_console(self, args: List[Any]) -> None:
        """
        Configures SettingsManager by accessing the console and retrieving the arguments used to run the script.
        :param args: either console arguments from sys.argv or spoofed ones
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
        self.__console_arguments.parse_args(args=args, namespace=self)


# Global configuration
# ---
options = SettingsManager()

# Add some common options
options.arg_console.add_argument(
    '--version',
    action='version',
    version='%(prog)s 3.0'
)
