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

    # Set up the builders
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
    # Run the main program, which outputs the entries
    # ---
    Librarian(
        cli_options.filepath,
        cli_options.destination,
        entries_from_builder=file_template
    ).output_all()


if __name__ == '__main__':
    try:
        main()
    # Custom application return codes should be within this range:
    # "150-199	reserved for application use" - as per: https://docs.python.org/3/library/sys.html#sys.exit
    # also: "Unix programs generally use 2 for command line syntax errors and 1 for all other kind of errors"
    # 2 is reserved for argparse error
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("KeyboardInterrupt received, exiting gracefully.")
        sys.exit(150)
    except CannotAccessJournalError as err:
        # Invoking help() instead of writing it directly just helps to cut down on duplicate strings
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(151)
    except EmptyJournalError as err:
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(152)
