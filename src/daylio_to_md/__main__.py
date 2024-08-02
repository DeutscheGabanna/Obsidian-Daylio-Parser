import sys
import logging

from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.group import EntriesFromBuilder
from daylio_to_md.config import parse_console
from daylio_to_md.librarian import Librarian, CannotAccessJournalError, EmptyJournalError


def main():
    """Parse a Daylio CSV into an Obsidian-compatible .MD file"""
    # Compile global settings
    # ---
    # Read arguments from console and update the global_settings accordingly
    cli_options = parse_console(sys.argv[1:])  # [1:] skips the program name, such as ["foo.py", ...]

    # And now let's start processing
    # ---
    entry_template = EntryBuilder(
        cli_options.csv_delimiter,
        cli_options.header_level,
        cli_options.tag_activities,
        cli_options.prefix,
        cli_options.suffix
    )
    file_template = EntriesFromBuilder(
        cli_options.front_matter_tags,
        entry_template
    )
    Librarian(
        cli_options.filepath,
        cli_options.destination,
        entries_from_builder=file_template
    ).output_all()


if __name__ == '__main__':
    try:
        main()
    except CannotAccessJournalError as err:
        # Invoking help() instead of writing it directly just helps to cut down on duplicate strings
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(1)
    except EmptyJournalError as err:
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(2)
