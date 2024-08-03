"""
Librarian is a Director type class. It creates and initialises other builder objects - e.g. DatedEntriesGroup.
It sets up the process, parses the CSV file and passes extracted values to DatedEntriesGroup.
Imagine Librarian is an actual person, reading the contents of the file out-loud to a scribe (DatedEntriesGroup).
Each date is a different scribe, but they all listen to the same Librarian.
Librarian knows their identity and can call upon them when needed to recite their contents back to the Librarian.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:

└── **ALL NOTES**
 └── a file from specific day
  └── an entry from that day
"""
from __future__ import annotations

import os
import shutil
import typing
import filecmp
import logging
import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from daylio_to_md import entry
from daylio_to_md import utils, errors
from daylio_to_md.group import EntriesFrom, EntriesFromBuilder
from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.utils import CsvLoader, CouldNotLoadFileError, guess_date_type, ensure_dir, InvalidDataInFileError

"""---------------------------------------------------------------------------------------------------------------------
ERRORS
---------------------------------------------------------------------------------------------------------------------"""


class ErrorMsg(errors.ErrorMsgBase):
    FILE_INCOMPLETE = "{} is incomplete."
    FILE_EMPTY = "{} is empty."
    FILE_MISSING = "{} does not exist."
    PERMISSION_ERROR = "Cannot access {}."
    STANDARD_MOODS_USED = "Standard mood set (rad, good, neutral, bad, awful) will be used."
    DECODE_ERROR = "Error while decoding {}"
    NOT_A_FILE = "{} is not a file."
    COUNT_ROWS = "{} rows of data found in {}. Of that {} were processed correctly."


class CannotAccessJournalError(utils.CouldNotLoadFileError):
    """The journal .csv {} could not be accessed or parsed."""

    def __init__(self, path: str):
        super().__init__(path)


class EmptyJournalError(utils.CouldNotLoadFileError):
    """The journal .csv {} did not produce any valid journal entries."""

    def __init__(self, path: str):
        super().__init__(path)


# FIXME: unused exception - Librarian will never know the custom .json failed because utils never let it know
class CannotAccessCustomMoodsError(utils.CouldNotLoadFileError):
    """The custom moods .json {} could not be accessed or parsed."""

    def __init__(self, path: str):
        super().__init__(path)


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""
# I've found a term that describes what this class does - it is a Director - even sounds similar to Librarian
# https://refactoring.guru/design-patterns/builder


class Librarian:
    """
    Orchestrates the entire process of parsing CSV & passing data to objects specialised to handle it as a journal.
    The chain of command looks like this:

    ``Librarian`` -> :class:`DatedEntriesGroup` -> :class:`DatedEntries`

    How to process the CSV
    ----------------------
    User only needs to instantiate this object and pass the appropriate arguments.
    The processing does not require invoking any other functions. Functions of this class are therefore mostly private.

    How to output the journal
    -------------------------
    Call :func:`output_all` method.
    """

    def __init__(self,
                 path_to_file: str,
                 path_to_output: str = None,
                 path_to_moods: str = None,
                 force_overwrite: bool = None,
                 entries_from_builder: EntriesFromBuilder = EntriesFromBuilder(),
                 entry_builder: EntryBuilder = EntryBuilder()):
        """
        :param path_to_file: The path to the CSV file for processing.
        :param path_to_output: The path for outputting processed data as markdown files.
               If user does not provide the output path, no output functionality will work.
        :param path_to_moods: The path for a custom mood set file.
        :raises CannotAccessFileError: if any problems occur during accessing or decoding the CSV file.
        :raises EmptyJournalError: if the file does not produce any valid results after processing.
        """
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__filepath = path_to_file
        self.__known_dates: dict[datetime.date, EntriesFrom] = {}
        self.__entries_from_builder = entries_from_builder
        self.__entry_builder = entry_builder
        self.__force_overwrite = force_overwrite

        self.__start(path_to_file, path_to_output, path_to_moods)

    def __start(self,
                path_to_file: str,
                path_to_output: str,
                path_to_moods: str):
        # Let's start processing the file
        # ---
        # 1. Parse the path_to_moods JSON for a custom mood set
        # This method either returns custom moods or sets the defaults in case of problems
        # P.S Why am I starting first with moods? Because process_file first checks if it has moods installed.
        self.__mood_set = entry.mood.create_from(path_to_moods)

        # 2. Access the CSV file and get all the rows with content
        #    then pass the data to specialised data objects that can handle them in a structured way
        try:
            if self.__process_file(path_to_file)[0] == 0:
                raise EmptyJournalError(path_to_file)
        except (CouldNotLoadFileError, InvalidDataInFileError) as err:
            raise CannotAccessJournalError(path_to_file) from err

        # Ok, if no exceptions were raised so far, the file is good, let's go through the rest of the attributes
        self.__destination = path_to_output

    def __process_file(self, filepath: str) -> typing.Tuple[int, int]:
        """
        Validates CSV file and processes it into iterable rows.
        :param filepath: path to CSV to be read
        :raises CannotAccessFileError: if any problems occur during accessing the CSV file.
        :raises InvalidDataInFileError: if any problems occur during parsing the CSV file.
        :returns: ``[lines_parsed_correctly, all_lines_parsed]``
        """
        if not self.__mood_set.get_custom_moods:
            self.__logger.info(ErrorMsg.STANDARD_MOODS_USED)

        # Open file
        # ---
        # Let the custom context manager deal with the specific exceptions
        try:
            with CsvLoader().load(filepath) as file:
                # Processing
                # ---
                lines_parsed = 0
                lines_parsed_successfully = 0
                for raw_line in file:
                    raw_line: dict[str, str]
                    lines_parsed += 1

                    try:
                        # First, simple validation
                        validated_line = utils.validate_line(raw_line)
                        # Second validation done by more specialised classes in their __inits__
                        entries_from_this_date = self.__entries_from_builder.build(
                            validated_line["full_date"],
                            self.__mood_set
                        )
                        entries_from_this_date.create_entry(validated_line)
                        # Remember this date
                        self[entries_from_this_date.date] = entries_from_this_date
                    except (utils.IncompleteDataRow,
                            utils.TooManyCellsInRowError,
                            utils.InvalidDateError,
                            utils.InvalidTimeError) as err:
                        self.__logger.warning(err.__doc__)
                        continue
                    else:
                        lines_parsed_successfully += 1
        except ValueError as err:
            raise CannotAccessJournalError(filepath) from err

        # Report back how many lines were parsed successfully out of all tried
        self.__logger.info(ErrorMsg.COUNT_ROWS.format(lines_parsed, filepath, lines_parsed_successfully))
        return lines_parsed_successfully, lines_parsed

    def output_all(self) -> tuple[int, int, int]:
        """
        Loops through known dates and calls each :class:`EntriesFrom` to output its contents inside the destination.
        :returns: # of entries asked to output contents, # of overwrites, # of skipped overwrites
        """
        files_total = 0
        files_overwritten = 0
        files_skipped = 0

        for known_date in self.__known_dates.values():
            filepath = known_date.path(self.__destination)
            # path does not exist
            if not os.path.exists(filepath):
                ensure_dir(filepath)
                with Path(filepath).open(mode='w', encoding='UTF-8') as file:
                    known_date.output(file)
                    files_total += 1
                    continue

            # path exists
            with NamedTemporaryFile(mode='w', encoding='UTF-8') as temp_file:
                known_date.output(temp_file)
                temp_file.flush()

                # no changes detected
                if filecmp.cmp(temp_file.name, filepath):
                    self.__logger.info(f"{filepath.name} would be unchanged and was skipped.")
                    files_skipped += 1
                    continue

                user_confirmed = None
                if self.__force_overwrite is None:
                    print(f"{filepath} already exists and differs from what has been created based on the CSV.\n"
                          f"Overwrite the file with new content? (y/N)")
                    user_confirmed = True if input().strip().lower() == 'y' else False

                # do not overwrite and skip
                if self.__force_overwrite == 'reject' or user_confirmed is False:
                    self.__logger.info(f"{filepath} was skipped.")
                    files_skipped += 1
                    continue

                # overwrite
                try:
                    shutil.copyfile(temp_file.name, filepath)
                except shutil.SameFileError:
                    self.__logger.warning("filecmp and shutil can't agree whether the file would be changed!")
                    files_skipped += 1
                    continue
                except OSError:
                    self.__logger.info(f"Cannot write to {os.path.dirname(filepath)}, skipping {filepath.name}.")
                    files_skipped += 1
                    continue
                else:
                    self.__logger.info(f"Successfully overwritten {filepath.name}.")
                    files_overwritten += 1
                    continue

        print(f"\nCreated {files_total} {'file' if files_total == 1 else 'files'} "
              f"and overwritten {files_overwritten} that already existed. "
              f"{files_skipped} {'file' if files_skipped == 1 else 'files'} were skipped.")
        if self.__force_overwrite is not None:
            print(f"Used {'auto-overwrite' if self.__force_overwrite else 'auto-skip'} on all conflicts.")

        return files_total, files_overwritten, files_skipped

    def __getitem__(self, key: typing.Union[datetime.date, str, typing.List[str], typing.List[int]]) -> EntriesFrom:
        """
        Accesses an already existing :class:`EntriesFrom` for the specified ``key`` as target date.
        e.g.::

            my_librarian[datetime.date(2022, 10, 10)]
            my_librarian["2022-10-10"]
            my_librarian[[2022, 10, 10]]

        :raises KeyError: if key cannot be found in the dictionary of known dates.
        :return: reference to :class:`DatedEntriesGroup` object
        """
        date_lookup: datetime.date = guess_date_type(key)

        if date_lookup in self.__known_dates:
            return self.__known_dates[date_lookup]
        # TODO: custom exception like EntryMissingError
        raise KeyError

    def __setitem__(self,
                    key: typing.Union[datetime.date, str, typing.List[str], typing.List[int]],
                    value: EntriesFrom):
        """
        :param key: any of the three types that can be type-casted into valid :class:`datetime.date` object
        :param value: :class:`EntriesFrom` object
        :raise TypeError: if key cannot be coerced into proper object type or there is a type mismatch
        """
        if not isinstance(value, EntriesFrom):
            raise TypeError
        date = guess_date_type(key)
        self.__known_dates[date] = value

    @property
    def mood_set(self):
        return self.__mood_set

    def __repr__(self):
        total_entries = sum(len(entries_on_that_day) for entries_on_that_day in self.__known_dates.values())
        str_entries_from = [str(this_entry) for this_entry in self.__known_dates.keys()]
        return (f"{self.__class__.__name__}("
                f"from={self.__filepath}, "
                f"to={self.__destination}, "
                f"total_entries={total_entries}, "
                f"entries_from={str_entries_from})")
