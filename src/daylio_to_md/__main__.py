import logging
import sys
from typing import Annotated

import typer

from daylio_to_md.group import EntriesFromBuilder
from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.librarian import Librarian, CannotAccessJournalError, EmptyJournalError

app = typer.Typer()

@app.command()
def main(
        filepath: Annotated[str, typer.Argument(
            help="Path to the Daylio .CSV file"
        )],
        destination: Annotated[str, typer.Argument(
            help="Path to folder to output finished files into."
        )],
        csv_delimiter: Annotated[str, typer.Option(
            help="Character used by Daylio .CSV to separate each cell, e.g: football | chess",
            rich_help_panel="How to parse csv"
        )] = '|',
        header_level: Annotated[int, typer.Option(
            min=1, max=6,
            help="Heading level to use for entries",
            rich_help_panel="How to print markdown"
        )] = 2,
        # you need ["daylio"] not "daylio" because otherwise tuple does this: ('d', 'a', 'y', 'l', 'i', 'o')
        front_matter_tags: Annotated[tuple[str], typer.Option(
            help="Tags to always include in the front-matter",
            rich_help_panel="How to print markdown"
        )] = tuple(["daylio"]),
        prefix: Annotated[str, typer.Option(
            help="String to always begin each entry heading with",
            rich_help_panel="How to print markdown"
        )] = "",
        suffix: Annotated[str, typer.Option(
            help="String to always end each entry heading with",
            rich_help_panel="How to print markdown"
        )] = "",
        tag_activities: Annotated[bool, typer.Option("--tag-activities",
            help="Convert activities into valid front-matter tags",
            rich_help_panel="How to print markdown"
        )] = True,
        colour: Annotated[bool, typer.Option("--color",
            help="Prepend a colour emoji to each entry depending on mood",
            rich_help_panel="How to print markdown"
        )] = False,
        force: Annotated[bool, typer.Option("--force",
            help="Instead of asking for confirmation every time when overwriting files, accept or refuse all such "
             "requests."
        )] = False
):
    """Parse a Daylio CSV into an Obsidian-compatible .MD file"""

    # And now let's start processing
    # ---
    entry_template = EntryBuilder(
        csv_delimiter,
        header_level,
        tag_activities,
        prefix,
        suffix
    )
    file_template = EntriesFromBuilder(
        front_matter_tags,
        entry_template
    )
    Librarian(
        filepath,
        destination,
        entries_from_builder=file_template
    ).output_all()

# Without this intermediary function pyproject.toml cannot make a CLI entry-point for the program
# because if it points to __main__.main() then it won't have Typer working
# relevant discussion: https://github.com/fastapi/typer/issues/34
def run():
    app()


if __name__ == '__main__':
    try:
        run()
    except CannotAccessJournalError as err:
        # Invoking help() instead of writing it directly just helps to cut down on duplicate strings
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(1)
    except EmptyJournalError as err:
        logging.getLogger(__name__).critical(err.__doc__)
        sys.exit(2)
