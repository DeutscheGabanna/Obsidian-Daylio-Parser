import sys
import logging

from daylio_to_md.config import options
from daylio_to_md.librarian import Librarian, CannotAccessFileError


def main():
    """Parse a Daylio CSV into an Obsidian-compatible .MD file"""
    # Compile global settings
    # ---
    # Read arguments from console and update the global_settings accordingly
    options.parse_console(sys.argv[1:])  # [1:] skips the program name, such as ["foo.py", ...]

    # And now let's start processing
    # ---
    Librarian(path_to_file=options.filepath, path_to_output=options.destination).output_all()


if __name__ == '__main__':
    try:
        main()
    except CannotAccessFileError as err:
        # Invoking help() instead of writing it directly just helps to cut down on duplicate strings
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(1)
