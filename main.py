"""Parse a Daylio CSV into an Obsidian-compatible .MD file"""
import logging
import os
# Other
import parse_csv
import compile_md
import write_md
import utils
import cmd_args

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a custom handler for console output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter for the log messages
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

# SETTING THE EXPORT DIRECTORY
parsed_path = utils.expand_path(cmd_args.settings.destination)
logger.info("Checking if destination %s exists...", parsed_path)
if not os.path.isdir(parsed_path):
    os.makedirs(cmd_args.settings.destination)
    logger.info("Destination missing... Created")
else:
    logger.info("Destination exists...")

# Parse rows into dictionary of days, where each day can have multiple Entry objects
days = parse_csv.setup(
    utils.expand_path(cmd_args.settings.filepath)
)
logger.info(
    "Parsed %d unique days with %d entries in total",
    len(days),
    sum(len(array) for array in days.values())
)

for day, entries in days.items():
    note_contents = compile_md.compile_note_YAML()
    for current_entry in entries:
        note_contents += compile_md.compile_entry_contents(current_entry)
    current_note = write_md.Note(day, note_contents)
    try:
        current_note.create_file()
    except PermissionError:
        logger.debug("User refused to overwrite the file.")
