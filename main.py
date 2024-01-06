"""Parse a Daylio CSV into an Obsidian-compatible .MD file"""
import logging
import sys

from config import options
from librarian import Librarian

logger = logging.getLogger(__name__)

# Compile global settings
# ---
# Read arguments from console and update the global_settings accordingly
options.parse_console(sys.argv[1:])  # [1:] skips the program name, such as ["foo.py", ...]

# And now let's start processing
# ---
Librarian(path_to_file=options.filepath)
