from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer

from obsidian_daylio_parser.entry.mood import Moodverse
from obsidian_daylio_parser.group import EntriesFromBuilder
from obsidian_daylio_parser.journal_entry import EntryBuilder
from obsidian_daylio_parser.librarian import Librarian, CannotAccessJournalError, EmptyJournalError
from obsidian_daylio_parser.logs import logger
from obsidian_daylio_parser.reader import CsvJournalReader
from obsidian_daylio_parser.writer import MarkdownWriter

app = typer.Typer()

import importlib.metadata

__version__ = importlib.metadata.version("obsidian-daylio-parser")


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()


@app.command()
def main(
        # Don't use PathLike even if it is better because Typer can't support it yet
        filepath: Annotated[Path, typer.Argument(
            exists=True, readable=True, file_okay=True, dir_okay=False,
            help="Path to the Daylio .CSV file"
        )],
        destination: Annotated[Path, typer.Argument(
            exists=True, readable=True, file_okay=False, dir_okay=True, writable=True,
            help="Path to folder to output finished files into."
        )],
        custom_moods: Annotated[Path, typer.Option(
            exists=True, readable=True, file_okay=True, dir_okay=False,
            help="Path to a .json file that contains custom moods. Otherwise defaults will be used."
        )] = None,
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
        version: Annotated[
            bool | None, typer.Option("--version", "-v", callback=version_callback)
        ] = None,
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

    # Assemble the pipeline via dependency injection
    # ---
    reader = CsvJournalReader(filepath)
    mood_set = Moodverse.from_file(custom_moods)
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

    # Run the main program: parse the journal, then write it out
    # ---
    journal = Librarian(reader, mood_set, file_template).parse()
    MarkdownWriter(destination).write_all(journal)


# Without this intermediary function pyproject.toml cannot make a CLI entry-point for the program
# because if it points to __main__.main() then it won't have Typer working
# relevant discussion: https://github.com/fastapi/typer/issues/34
def run():
    app()


if __name__ == '__main__':
    try:
        run()
    # Custom application return codes should be within this range:
    # "150-199	reserved for application use" - as per: https://docs.python.org/3/library/sys.html#sys.exit
    # also: "Unix programs generally use 2 for command line syntax errors and 1 for all other kind of errors"
    # 2 is reserved for argparse error
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, exiting gracefully.")
        sys.exit(150)
    except CannotAccessJournalError as err:
        logger.critical(err.__doc__)
        sys.exit(151)
    except EmptyJournalError as err:
        logger.critical(err.__doc__)
        sys.exit(152)
