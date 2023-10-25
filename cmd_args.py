"""Sets up all necessary options and arguments for main.py"""
import argparse

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
    help="Path to output finished files into."
)
parser.add_argument(
    "--prefix", # <here's your prefix>YYYY-MM-DD.md so remember about a separating char
    default='',
    help="Prepends a given string to each entry's header."
)
parser.add_argument(
    "--suffix", # YYYY-MM-DD<here's your suffix>.md so remember about a separating char
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
parser.add_argument('--version', action='version', version='%(prog)s 2.0')
parser.add_argument(
    "--header",
    type=int,
    default=2,
    help="Headings level for each entry.",
    dest="HEADER_LEVEL"
)
parser.add_argument(
    "--tags",
    help="Tags in the YAML metamood_to_check of each note.",
    default="daily",
    dest="TAGS"
)
# TODO: Force-argument does nothing yet.
parser.add_argument(
    "--force",
    choices=["accept", "refuse"],
    help="Skips user confirmation when overwriting files. Either force 'accept' (DANGEROUS!) or 'refuse' all requests."
)
parser.add_argument(
    "--csv-delimiter",
    default="|",
    help="Set delimiter for activities in Daylio .CSV, e.g: football | chess"
)
# TODO: User should be able to set verbosity level in logging
 
settings = parser.parse_args()
