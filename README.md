# Obsidian Daylio Parser

Convert your [Daylio](https://daylio.net/) journal backup (`.csv`) into Markdown files for [Obsidian](https://obsidian.md/).

![Daylio to Obsidian](https://user-images.githubusercontent.com/59067099/198896455-41bb9496-7efc-4102-b311-f1db614a2d96.png)

## What it does

Daylio lets you export your journal as a `.csv` file. This tool reads that export and produces one `.md` file per day, organised into `year/month/` sub-directories — ready to drop into an Obsidian vault.

Each output file contains YAML front matter and one or more journal entries:

```
---
tags: daylio
---

## captivated | 22:00
#at-the-office #board-game #colleague-interaction
Sed ut est interdum

## tired | 20:00 | An optional title
#allegro #at-the-office #board-game
Quisque dictum odio quis augue consectetur.
```

### Features

- Groups multiple entries from the same day into a single `.md` file
- Converts activities into Obsidian-compatible `#tags` (slugified, lowercased, special characters stripped)
- Supports custom mood sets via a `.json` file for mood-group colour coding
- Supports non-Latin characters in notes and activities (Polish, Cyrillic, etc.)
- Configurable YAML front-matter tags, heading levels, and entry prefixes/suffixes

## Installation

### pip (recommended)

```bash
pip install daylio-obsidian-parser
```

### From source

```bash
git clone https://github.com/DeutscheGabanna/Obsidian-Daylio-Parser.git
cd Obsidian-Daylio-Parser
pip install .
```

### Docker

```bash
docker build -t daylio-parser .
docker run -v /path/to/your/files:/data daylio-parser /data/export.csv /data/output
```

## Usage

```bash
daylio_to_md <filepath> <destination> [options]
```

### Arguments

| Argument | Description |
|---|---|
| `filepath` | Path to the Daylio `.csv` export file |
| `destination` | Output folder. Files are organised into `destination/year/month/YYYY-MM-DD.md` |

### Options

| Option | Default | Description |
|---|---|---|
| `--version` | | Show the installed version and exit |
| `--force accept\|refuse` | *(prompt)* | Accept or refuse all overwrite confirmations without asking |
| `--front_matter_tags TAG [TAG ...]` | `daylio` | Tags for the YAML front matter of each `.md` file |
| `--prefix TEXT` | *(empty)* | Prepend a string to each entry's header |
| `--suffix TEXT` | *(empty)* | Append a string to each entry's header |
| `--tag_activities`, `-a` | `True` | Convert activities into `#tag` format |
| `--color` | *(unused)* | Intended for mood colour coding — **not yet implemented** |
| `--header N` | `2` | Heading level for entries (e.g. `2` → `##`, `3` → `###`) |
| `--csv-delimiter CHAR` | `\|` | Delimiter separating activities *within* a single CSV cell |

### Examples

Basic conversion:

```bash
daylio_to_md ~/Downloads/daylio_export.csv ~/ObsidianVault/Journal
```

Custom front-matter tags with `###` headings:

```bash
daylio_to_md export.csv ./vault --front_matter_tags journal mood-tracking --header 3
```

Activities as plain text (no `#` prefix):

```bash
daylio_to_md export.csv ./vault --tag_activities False
```

## Custom moods

By default, Daylio uses five mood groups: **rad**, **good**, **neutral**, **bad**, and **awful**. Each group maps to exactly one mood of the same name.

To use your own expanded mood vocabulary, create a `.json` file with the five mood groups as keys, each containing an array of mood names:

```json
{
    "rad": ["rad", "blissful", "excited"],
    "good": ["vaguely good", "grateful", "captivated"],
    "neutral": ["vaguely ok", "focused", "bored"],
    "bad": ["frustrated", "anxious", "drained"],
    "awful": ["awful", "lifeless", "miserable"]
}
```

Only the five standard group keys (`rad`, `good`, `neutral`, `bad`, `awful`) are recognised. Unknown keys are silently ignored. Duplicate and empty mood names are skipped.

> **Note:** Custom moods can be passed via `path_to_moods` when using the library programmatically. There is currently no CLI flag for this.

## Expected CSV format

The converter expects the standard Daylio CSV export format:

```csv
full_date,date,weekday,time,mood,activities,note_title,note
2022-10-26,October 26,Wednesday,10:00 PM,captivated,at the office | board game,,"Sed ut est interdum"
```

All columns must be present. `activities`, `note_title`, and `note` may be empty.

> **Note:** Newer versions of Daylio may include a `scales` column in the export. Scales are not yet supported and may cause issues since the parser currently expects exactly 8 columns.

## Known limitations

- **`--force` is not yet implemented.** The flag is accepted by the parser but has no effect — files are always silently overwritten.
- **`--color` is not yet implemented.** The flag is accepted but mood colour coding is not applied.
- **No CLI flag for custom moods.** Custom mood sets can only be used through the Python API, not from the command line.
- **Scales are not supported.** The `scales` column introduced in newer Daylio exports is not parsed.
- **Entries at the same time on the same day are overwritten.** If two entries share the exact same date and time, only the last one in the CSV is kept.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `2` | Invalid command-line arguments (argparse) |
| `150` | Keyboard interruption |
| `151` | Cannot access or parse the `.csv` file |
| `152` | The `.csv` produced no valid journal entries |

## Project structure

```
src/daylio_to_md/
├── __main__.py        # CLI entry point
├── config.py          # Argument parsing and defaults
├── errors.py          # Logging setup and base error classes
├── group.py           # EntriesFrom — groups entries by date, outputs .md
├── journal_entry.py   # Entry — a single journal entry
├── librarian.py       # Librarian — orchestrates CSV parsing and file output
├── utils.py           # Date/time parsing, slugify, file loaders
└── entry/
    └── mood.py        # Moodverse — mood group management
```

## Development

```bash
git clone https://github.com/DeutscheGabanna/Obsidian-Daylio-Parser.git
cd Obsidian-Daylio-Parser
pip install pipenv
pipenv install --dev
```

### Running tests

```bash
pipenv run coverage run -m unittest discover -s . -t .
```

### Linting

```bash
pip install flake8
flake8 src/
```

## Requirements

- Python ≥ 3.8

## License

[GPL-3.0](LICENSE)

