"""Parse a Daylio CSV into an Obsidian-compatible .MD file"""
import logging
import os

import config
import utils
from librarian import Librarian

logger = logging.getLogger(__name__)
main_config = config.create_parser().parse_args()

# SETTING THE EXPORT DIRECTORY
parsed_path = utils.expand_path(main_config.destination)
logger.info("Checking if destination %s exists...", parsed_path)
if not os.path.isdir(parsed_path):
    os.makedirs(main_config.destination)
    logger.info("Destination missing... Created")
else:
    logger.info("Destination exists...")

Librarian(
    path_to_file="_tests/sheet-1-valid-data.csv",
    path_to_moods="moods.json",
    custom_config=main_config)

# for day, entries in days.items():
#     note_contents = compile_md.compile_note_yaml()
#     for current_entry in entries:
#         note_contents += compile_md.compile_entry_contents(current_entry)
#     current_note = write_md.Note(day, note_contents)
#     try:
#         current_note.create_file()
#     except PermissionError:
#         logger.debug("User refused to overwrite the file.")
