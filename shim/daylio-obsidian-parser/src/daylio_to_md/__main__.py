"""Compatibility CLI that forwards to obsidian_daylio_parser."""
from __future__ import annotations

import sys

from obsidian_daylio_parser.__main__ import main as canonical_main


def main() -> int | None:
    print(
        "DEPRECATED: 'daylio-obsidian-parser' and 'daylio_to_md' are deprecated. "
        "Use 'obsidian-daylio-parser' instead. Sorry for creating so many variants in the first place.",
        file=sys.stderr,
    )
    return canonical_main()


if __name__ == "__main__":
    raise SystemExit(main())
