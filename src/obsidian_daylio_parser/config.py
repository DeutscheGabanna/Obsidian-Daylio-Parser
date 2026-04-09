"""
Sets up all necessary options and arguments.
.
├── Librarian/
│   ├── processing/
│   │   └── filepath
│   └── outputting/
│       ├── destination
│       └── force
|
├── DatedGroup/
│   ├── processing
│   └── outputting
|
└── DatedEntries/
    ├── processing/
    │   └── csv_delimiter
    └── outputting/
        ├── prefix
        ├── suffix
        ├── colour
        └── header

"""
from __future__ import annotations

# https://www.doc.ic.ac.uk/~nuric/posts/coding/how-to-handle-configuration-in-python/

import argparse
import logging
from importlib.metadata import version, PackageNotFoundError # https://versioningit.readthedocs.io/en/stable/runtime-version.html
from collections import namedtuple
from typing import List, Any

try:
    __version__ = version("obsidian-daylio-parser")
except PackageNotFoundError:
    # Fallback for development/testing in workflow runners
    # otherwise --> importlib.metadata.PackageNotFoundError: No package metadata was found for obsidian-daylio-parser
    __version__ = "dev"

# Logging for config library
logger = logging.getLogger(__name__)

# I chose namedtuple for immutability
DefaultSettings = namedtuple('DefaultSettings', [
    "filepath",
    "destination",
    "force",
    "csv_delimiter",
    "header_level",
    "front_matter_tags",
    "prefix",
    "suffix",
    "tag_activities",
    "colour"
])
DEFAULTS = DefaultSettings(None, None, None, '|', 2, tuple(["daylio"]), '', '', True, bool)