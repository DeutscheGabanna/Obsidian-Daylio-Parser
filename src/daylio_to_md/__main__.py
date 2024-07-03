import logging
import sys

from daylio_to_md.config import options
from daylio_to_md.librarian import Librarian


def main():
    """Parse a Daylio CSV into an Obsidian-compatible .MD file"""
    logger = logging.getLogger(__name__)

    # Compile global settings
    # ---
    # Read arguments from console and update the global_settings accordingly
    options.parse_console(sys.argv[1:])  # [1:] skips the program name, such as ["foo.py", ...]

    # And now let's start processing
    # ---
    Librarian(path_to_file=options.filepath, path_to_output=options.destination).output_all()


if __name__ == '__main__':
    main()
