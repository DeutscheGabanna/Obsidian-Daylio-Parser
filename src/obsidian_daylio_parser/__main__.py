import sys
import logging

from obsidian_daylio_parser.journal_entry import EntryBuilder
from obsidian_daylio_parser.group import EntriesFromBuilder
from obsidian_daylio_parser.config import parse_console
from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.reader import CsvJournalReader
from obsidian_daylio_parser.writer import MarkdownWriter
from obsidian_daylio_parser.librarian import Librarian, CannotAccessJournalError, EmptyJournalError


def main():
    """Parse a Daylio CSV into an Obsidian-compatible .MD file"""
    # Compile global settings
    # ---
    # Read arguments from console and update the global_settings accordingly
    cli_options = parse_console(sys.argv[1:])  # [1:] skips the program name, such as ["foo.py", ...]

    # Assemble the pipeline via dependency injection
    # ---
    reader = CsvJournalReader(cli_options.filepath)
    mood_set = Moodverse.from_file(getattr(cli_options, 'moods', None))
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

    # Run the main program: parse the journal, then write it out
    # ---
    journal = Librarian(reader, mood_set, file_template).parse()
    MarkdownWriter(cli_options.destination).write_all(journal)


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
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(151)
    except EmptyJournalError as err:
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(152)
