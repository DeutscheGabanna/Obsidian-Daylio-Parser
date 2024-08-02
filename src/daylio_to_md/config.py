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
from __future__ import annotations

# https://www.doc.ic.ac.uk/~nuric/posts/coding/how-to-handle-configuration-in-python/

import argparse
import logging
from collections import namedtuple
from typing import List, Any

# Logging for config library
logger = logging.getLogger(__name__)

# I chose namedtuple for immutability
DefaultSettings = namedtuple('DefaultSettings', [
    "filepath",
    "destination",
    "force",
    "csv_delimiter",
    "header_level",
    "front_matter_tags",
    "prefix",
    "suffix",
    "tag_activities",
    "colour"
])
DEFAULTS = DefaultSettings(None, None, None, '|', 2, tuple(["daylio"]), '', '', True, bool)


def parse_console(args: List[Any]) -> argparse.Namespace:
    """
    Parses the list as if it were a list of arguments given to a script.
    :param args: either console arguments from sys.argv or spoofed ones
    """
    console_arguments = argparse.ArgumentParser(
        fromfile_prefix_chars="@",
        prog="Daylio to Obsidian Parser",
        description="Converts Daylio .CSV backup file into Markdown files for Obsidian.",
        epilog="Created by DeutscheGabanna"
    )
    console_arguments.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.3'
    )
    """-------------------------------------------------------------------------------------------------------------
    ADD MAIN SETTINGS TO ARGPARSE
    -------------------------------------------------------------------------------------------------------------"""
    # Adding Librarian-specific options in global_settings
    main_settings = console_arguments.add_argument_group(
        "Main options"
    )
    # 1. Filepath is absolutely crucial to even start processing
    main_settings.add_argument(
        "filepath",
        type=str,
        help="Specify path to the .CSV file"
    )
    # 2. Destination is not needed if user is only processing, but no destination makes it impossible to output
    # that data.
    main_settings.add_argument(
        "destination",
        type=str,
        help="Path to folder to output finished files into."
    )
    # TODO: Force-argument does nothing yet.
    main_settings.add_argument(
        "--force",
        choices=["accept", "refuse"],
        default=DEFAULTS.force,
        help="Instead of asking for confirmation every time when overwriting files, accept or refuse all such "
             "requests."
    )
    """-------------------------------------------------------------------------------------------------------------
    FILE STRUCTURE SETTINGS TO ARGPARSE
    -------------------------------------------------------------------------------------------------------------"""
    file_structure_settings = console_arguments.add_argument_group(
        "File structure"
    )
    file_structure_settings.add_argument(
        "--front_matter_tags",
        help="Tags in the YAML of each note.",
        nargs='*',  # this allows, for example, "--frontmatter_tags one two three" --> ["one", "two", "three"]
        default=DEFAULTS.front_matter_tags,
        dest="front_matter_tags"
    )
    """-------------------------------------------------------------------------------------------------------------
    JOURNAL ENTRY FORMATTING SETTINGS TO ARGPARSE
    -------------------------------------------------------------------------------------------------------------"""
    # Adding DatedEntry-specific options in global_settings
    journal_entry_settings = console_arguments.add_argument_group(
        "Journal entry settings",
        "Handles how journal entries should be formatted"
    )
    journal_entry_settings.add_argument(
        "--prefix",  # <here's your prefix>YYYY-MM-DD.md so remember about a separating char
        default=DEFAULTS.prefix,
        help="Prepends a given string to each entry's header."
    )
    journal_entry_settings.add_argument(
        "--suffix",  # YYYY-MM-DD<here's your suffix>.md so remember about a separating char
        default=DEFAULTS.suffix,
        help="Appends a given string at the end of each entry's header."
    )
    journal_entry_settings.add_argument(
        "--tag_activities", "-a",
        default=DEFAULTS.tag_activities,
        help="Tries to convert activities into valid front-matter tags.",
        dest="tag_activities"
    )
    journal_entry_settings.add_argument(
        "-colour", "--color",
        default=DEFAULTS.colour,
        help="Prepends a colour emoji to each entry depending on mood.",
        dest="colour"
    )
    journal_entry_settings.add_argument(
        "--header",
        type=int,
        default=DEFAULTS.header_level,
        help="Headings level for each entry.",
        dest="header_level"
    )
    journal_entry_settings.add_argument(
        "--csv-delimiter",
        default=DEFAULTS.csv_delimiter,
        help="Set delimiter for activities in Daylio .csv, e.g: football | chess"
    )

    return console_arguments.parse_args(args=args)
