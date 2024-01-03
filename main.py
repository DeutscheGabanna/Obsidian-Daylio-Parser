"""Parse a Daylio CSV into an Obsidian-compatible .MD file"""
import logging
from config import options
from librarian import Librarian

logger = logging.getLogger(__name__)

# Compile global settings
# ---
# Read arguments from console and update the global_settings accordingly
options.get_console().parse_console()

# And now let's start processing
# ---
Librarian(path_to_file=options.settings.filepath)
