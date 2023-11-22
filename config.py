"""
Sets up all necessary options and arguments.
Librarian:
├── filepath
├── destination
└── force

DatedGroup:
└── tags

DatedEntries:
├── prefix (output)
├── suffix (output)
├── activities_as_tags (creation)
├── csv_delimiter
├── colour
└── header

You can either:
* config.get_defaults() to avoid any complains from argparse during testing
* create_parser().parse_args() if you're coding for an actual user scenario
The second option will require the program be started in a console environment with properly passed arguments.
"""
import argparse


def get_defaults():
    """
    Use this method to avoid any complains from argparse during testing by spoon-feeding two crucial arguments.
    """
    return create_parser().parse_args(
        ['sheet-1-valid-data.csv', '/output-results']
    )


def create_parser():
    """
    Use this method if you're coding for an actual user scenario. It actually requires a user to provide the arguments.
    """
    # noinspection SpellCheckingInspection
    parser = argparse.ArgumentParser(
        prog="Daylio to Obsidian Parser",
        description="Converts Daylio .CSV backup file into Markdown files for Obsidian.",
        epilog="Created by DeutscheGabanna"
    )
    parser.add_argument(
        "filepath",
        type=str,
        help="Specify path to the .CSV file"
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Path to output finished files into."
    )
    parser.add_argument(
        "--prefix",  # <here's your prefix>YYYY-MM-DD.md so remember about a separating char
        default='',
        help="Prepends a given string to each entry's header."
    )
    parser.add_argument(
        "--suffix",  # YYYY-MM-DD<here's your suffix>.md so remember about a separating char
        default='',
        help="Appends a given string at the end of each entry's header."
    )
    parser.add_argument(
        "--tag_activities", "-a",
        action="store_true",
        help="Tries to convert activities into valid tags.",
        dest="ACTIVITIES_AS_TAGS"
    )
    parser.add_argument(
        "-colour", "--color",
        action="store_true",
        help="Prepends a colour emoji to each entry depending on mood.",
        dest="colour"
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0'
    )
    parser.add_argument(
        "--header",
        type=int,
        default=2,
        help="Headings level for each entry.",
        dest="HEADER_LEVEL"
    )
    parser.add_argument(
        "--tags",
        help="Tags in the YAML of each note.",
        default="daily",
        dest="TAGS"
    )
    # TODO: Force-argument does nothing yet.
    parser.add_argument(
        "--force",
        choices=["accept", "refuse"],
        help="Skips user confirmation when overwriting files. Either force 'accept' or 'refuse' all requests."
    )
    parser.add_argument(
        "--csv-delimiter",
        default="|",
        help="Set delimiter for activities in Daylio .CSV, e.g: football | chess"
    )
    # TODO: User should be able to set verbosity level in logging

    return parser
