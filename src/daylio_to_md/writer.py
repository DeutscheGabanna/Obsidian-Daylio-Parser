"""
Writes a :class:`Journal` out to Markdown files.
Each day's entries become a separate ``.md`` file inside a ``year/month/`` directory structure.

To add support for a new output format, create a new writer class that accepts a :class:`Journal`.
"""
from __future__ import annotations

import os
from typing import IO

from daylio_to_md.journal import Journal


def _create_and_open(filename: str, mode: str) -> IO:
    """Create parent directories as needed, then open the file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return open(filename, mode, encoding="UTF-8")


class MarkdownWriter:
    """
    Writes each day's entries as a separate ``.md`` file.

    Directory layout::

        <destination>/<year>/<month>/<YYYY-MM-DD>.md

    Usage::

        MarkdownWriter("/output").write_all(journal)
    """

    def __init__(self, destination: str):
        self.__destination = destination

    def write_all(self, journal: Journal) -> None:
        """
        Loop through every day in the journal and write its entries to a Markdown file.
        :param journal: the parsed :class:`Journal` to output.
        """
        for entries_from in journal:
            date = entries_from.date
            filename = f"{date}.md"
            filepath = "/".join([
                self.__destination,
                str(date.year),
                str(date.month),
                filename
            ])
            # TODO: maybe add the mode option to settings in argparse? write/append
            with _create_and_open(filepath, 'w') as file:
                entries_from.output(file)

