"""
Librarian is a builder/singleton type class. It creates and initialises other builder objects - e.g. DatedEntriesGroup.
It sets up the process, parses the CSV file and passes extracted values to DatedEntriesGroup.
Imagine Librarian is an actual person, reading the contents of the file out-loud to a scribe (DatedEntriesGroup).
Each date is a different scribe, but they all listen to the same Librarian.
Librarian knows their identity and can call upon them when needed to recite their contents back to the Librarian.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:

``└── ALL NOTES``
    ``└── all notes written on a particular date``
        ``└── a particular note``
"""
from __future__ import annotations

import csv
import json
import os
import logging
from typing import IO

from daylio_to_md import utils, errors, dated_entries_group
from daylio_to_md.config import options
from daylio_to_md.dated_entries_group import DatedEntriesGroup
from daylio_to_md.entry.mood import Moodverse

# Adding Librarian-specific options in global_settings
librarian_settings = options.arg_console.add_argument_group(
    "Librarian",
    "Handles main options"
)
# 1. Filepath is absolutely crucial to even start processing
librarian_settings.add_argument(
    "filepath",
    type=str,
    help="Specify path to the .CSV file"
)
# 2. Destination is not needed if user is only processing, but no destination makes it impossible to output that data.
librarian_settings.add_argument(
    "destination",
    type=str,
    help="Path to folder to output finished files into."
)
# TODO: Force-argument does nothing yet.
librarian_settings.add_argument(
    "--force",
    choices=["accept", "refuse"],
    default=None,
    help="Skips user confirmation when overwriting files and auto-accepts or auto-refuses all requests."
)


class ErrorMsg(errors.ErrorMsgBase):
    FILE_INCOMPLETE = "{} is incomplete."
    FILE_EMPTY = "{} is empty."
    FILE_MISSING = "{} does not exist."
    PERMISSION_ERROR = "Cannot access {}."
    STANDARD_MOODS_USED = "Standard mood set (rad, good, neutral, bad, awful) will be used."
    DECODE_ERROR = "Error while decoding {}"
    NOT_A_FILE = "{} is not a file."
    CSV_ALL_FIELDS_PRESENT = "All expected columns are present in the CSV file columns."
    CSV_FIELDS_MISSING = "The following expected columns are missing: {}"
    COUNT_ROWS = "{} rows of data found in {}. Of that {} were processed correctly."


class MissingValuesInRowError(utils.CustomException):
    """If a CSV row does not have enough values needed to create an entry."""


class CannotAccessFileError(utils.CustomException):
    """The file could not be accessed."""


class CannotAccessJournalError(CannotAccessFileError):
    """The journal CSV could not be accessed or parsed."""


class CannotAccessCustomMoodsError(CannotAccessFileError):
    """The custom moods JSON could not be accessed or parsed."""


class InvalidDataInFileError(utils.CustomException):
    """The file does not follow the expected structure."""


class NoDestinationSelectedError(utils.CustomException):
    """You have not specified where to output the files when instantiating this Librarian object."""


def create_and_open(filename: str, mode: str) -> IO:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return open(filename, mode, encoding="UTF-8")


# I've found a term that describes what this class does - it is a Director - even sounds similar to Librarian
# https://refactoring.guru/design-patterns/builder
class Librarian:
    """
    Orchestrates the entire process of parsing CSV & passing data to objects specialised to handle it as a journal.
    The chain of command looks like this:

    ``Librarian`` -> :class:`DatedEntriesGroup` -> :class:`DatedEntries`

    ---

    **How to process the CSV**

    User only needs to instantiate this object and pass the appropriate arguments.
    The processing does not require invoking any other functions. Functions of this class are therefore mostly private.

    ---

    **How to output the journal**

    TODO: add missing documentation
    """

    def __init__(self,
                 path_to_file: str,  # the only crucial parameter at this stage
                 path_to_output: str = None,
                 path_to_moods: str = None):
        """
        :param path_to_file: The path to the CSV file for processing.
        :param path_to_output: The path for outputting processed data as markdown files.
         If user does not provide the output path, no output functionality will work.
        :raises CannotAccessFileError: if any problems occur during accessing or decoding the CSV file.
        :param path_to_moods: The path for a custom mood set file.
        """
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__known_dates: dict[str, DatedEntriesGroup] = {}

        # Let's start processing the file
        # ---
        # 1. Parse the path_to_moods JSON for a custom mood set, if possible, or otherwise use standard mood set
        #
        # P.S Why am I starting first with moods? Because process_file first checks if it has moods installed.
        try:
            self.__mood_set = self.__create_mood_set(path_to_moods)
        except CannotAccessFileError as err:
            raise CannotAccessCustomMoodsError from err

        # 2. Access the CSV file and get all the rows with content
        #    then pass the data to specialised data objects that can handle them in a structured way
        # TODO: Deal with files that are valid but at the end of parsing have zero lines successfully parsed
        try:
            self.__process_file(path_to_file)
        except (CannotAccessFileError, InvalidDataInFileError) as err:
            raise CannotAccessJournalError from err

        # Ok, if no exceptions were raised so far, the file is good, let's go through the rest of the attributes
        self.__destination = path_to_output

    def __create_mood_set(self, json_file: str = None) -> 'Moodverse':
        """
        Overwrite the standard mood-set with a custom one. Mood-sets are used in colour-coding each dated entry.

        :param json_file: path to the .JSON file with a non-standard mood set.
         Should have five keys: ``rad``, ``good``, ``neutral``, ``bad`` and ``awful``.
         Each of those keys should hold an array of any number of strings indicating various moods.
         **Example**: ``[{"good": ["good"]},...]``
        :returns: reference to the :class:`Moodverse` object
        """
        if json_file:
            exp_path = utils.expand_path(json_file)
            try:
                with open(exp_path, encoding="UTF-8") as file:
                    custom_mood_set_from_file = json.load(file)
            except FileNotFoundError as err:
                msg = ErrorMsg.print(ErrorMsg.FILE_MISSING, exp_path)
                self.__logger.warning(msg)
                raise CannotAccessFileError(msg) from err
            except PermissionError as err:
                msg = ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, exp_path)
                self.__logger.warning(msg)
                raise CannotAccessFileError(msg) from err
            except json.JSONDecodeError as err:
                msg = ErrorMsg.print(ErrorMsg.DECODE_ERROR, exp_path)
                self.__logger.warning(msg)
                raise CannotAccessFileError(msg) from err
        else:
            custom_mood_set_from_file = None

        # the command works with or without the argument
        # - Case 1: no argument = default mood-set
        # - Case 2: argument passed, but invalid = default mood-set
        # - Case 3: argument passed, it is valid = default mood-set expanded by the custom mood-set
        return Moodverse(custom_mood_set_from_file)

    # TODO: should return a tuple of { lines_processed_correctly, all_lines_processed }
    def __process_file(self, filepath: str) -> bool:
        """
        Validates CSV file and processes it into iterable rows.
        :param filepath: path to CSV to be read
        :raises CannotAccessFileError: if any problems occur during accessing the CSV file.
        :raises InvalidDataInFileError: if any problems occur during parsing the CSV file.
        :returns: True if parsed > 0, False otherwise
        """
        if not self.__mood_set.has_custom_moods:
            self.__logger.info(ErrorMsg.print(ErrorMsg.STANDARD_MOODS_USED))

        # Let's determine if the file can be opened
        # ---
        try:
            file = open(filepath, encoding='UTF-8')
        # File has not been found
        except FileNotFoundError as err:
            msg = ErrorMsg.print(ErrorMsg.FILE_MISSING, filepath)
            self.__logger.critical(msg)
            raise CannotAccessFileError(msg) from err
        # Insufficient permissions to access the file
        except PermissionError as err:
            msg = ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, filepath)
            self.__logger.critical(msg)
            raise CannotAccessFileError(msg) from err
        # Other error that makes it impossible to access the file
        except OSError as err:
            self.__logger.critical(OSError)
            raise CannotAccessFileError from err

        # If the code reaches here, the program can access the file.
        # Now let's determine if the file's contents are actually usable
        # ---

        with file:
            # Is it a valid CSV?
            try:
                # strict parameter throws csv.Error if parsing fails
                raw_lines = csv.DictReader(file, delimiter=',', quotechar='"', strict=True)
            except csv.Error as err:
                msg = ErrorMsg.print(ErrorMsg.DECODE_ERROR, filepath)
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg) from err

            # Does it have all the fields? Push any missing field into an array for later reference
            # Even if only one column from the list below is missing in the CSV, it's a problem while parsing later
            expected_fields = [
                "full_date",
                "date",
                "weekday",
                "time",
                "mood",
                "activities",
                "note",
                "note_title",
                "note"
            ]

            # Let's have a look at what columns we have in the parsed CSV
            # It seems that even files with random bytes occasionally pass through previous checks with no errors
            # Therefore this 'try' block is also necessary, we do not know if the entire file is now fault-free
            try:
                missing_strings = [
                    expected_field for expected_field in expected_fields if expected_field not in raw_lines.fieldnames
                ]
            except (csv.Error, UnicodeDecodeError) as err:
                msg = ErrorMsg.print(ErrorMsg.DECODE_ERROR, filepath)
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg) from err

            if not missing_strings:
                self.__logger.debug(ErrorMsg.print(ErrorMsg.CSV_ALL_FIELDS_PRESENT))
            else:
                msg = ErrorMsg.print(
                    ErrorMsg.CSV_FIELDS_MISSING,
                    ', '.join(missing_strings)  # which ones are missing - e.g. "date, mood, note"
                )
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg)

            # # Does it have any rows besides the header?
            # # If the file is empty or only has column headers, exit immediately
            # try:
            #     next(raw_lines)
            # except StopIteration:
            #     msg = ErrorMsg.print(ErrorMsg.FILE_EMPTY, filepath)
            #     self.__logger.critical(msg)
            #     raise InvalidDataInFileError(msg)

            # If the code has reached this point and has not exited, it means both file and contents have to be ok
            # Processing
            # ---
            lines_parsed = 0
            lines_parsed_successfully = 0
            for line in raw_lines:
                line: dict[str]
                try:
                    lines_parsed += self.__process_line(line)
                except MissingValuesInRowError:
                    pass
                else:
                    lines_parsed_successfully += 1

            # Report back how many lines were parsed successfully out of all tried
            self.__logger.info(ErrorMsg.print(
                ErrorMsg.COUNT_ROWS, str(lines_parsed), filepath, str(lines_parsed_successfully))
            )

            # If at least one line has been parsed, the following return resolves to True
            return bool(lines_parsed)

    # TODO: I guess it is more pythonic to raise exceptions than return False if I cannot complete the task
    # TODO: this has to be tested
    # https://eli.thegreenplace.net/2008/08/21/robust-exception-handling/
    def __process_line(self, line: dict[str]) -> bool:
        """
        Goes row-by-row and passes the content to objects specialised in handling it from a journaling perspective.
        :raises MissingValuesInRowError: if the row in CSV lacks enough commas to create 8 cells. It signals a problem.
        :param line: a dictionary with values from the currently processed CSV line
        :return: True if all columns had values for this CSV ``line``, False otherwise
        """
        # Does each of the 8 columns have values for this row?
        if len(line) < 8:
            # Oops, not enough values on this row, the file might be corrupted?
            msg = ErrorMsg.print(ErrorMsg.FILE_INCOMPLETE, str(line))
            self.__logger.warning(msg)
            raise MissingValuesInRowError(msg)
        # Let DatedEntriesGroup handle the rest and increment the counter (True == 1)
        try:
            self.access_date(line["full_date"]).create_dated_entry_from_row(line)
        except (dated_entries_group.TriedCreatingDuplicateDatedEntryError,
                dated_entries_group.IncompleteDataRow,
                dated_entries_group.InvalidDateError,
                ValueError):
            return False
        return True

    def access_date(self, target_date: str) -> DatedEntriesGroup:
        """
        Accesses an already existing or creates a new :class:`DatedEntriesGroup` for the specified ``target_date``.
        :raises ValueError: if ``target_date`` is an invalid Date as indicated by :class:`Date` object
        :param target_date: the date for which a unique :class:`DatedEntriesGroup` object should be created or accessed.
        :return: reference to :class:`DatedEntriesGroup` object
        """
        try:
            date_lookup = dated_entries_group.Date(target_date)
        except dated_entries_group.InvalidDateError as err:
            raise ValueError from err

        if str(date_lookup) in self.__known_dates:
            return self.__known_dates[str(date_lookup)]
        else:
            new_obj = DatedEntriesGroup(str(date_lookup), self.__mood_set)
            self.__known_dates[str(date_lookup)] = new_obj
            return new_obj

    def output_all(self):
        """
        Loops through known dates and calls :class:`DatedEntriesGroup` to output its contents inside the destination.
        :raises NoDestinationSelectedError: when the parent object has been instantiated without a destination set.
        """
        if self.__destination is None:
            raise NoDestinationSelectedError

        for known_date in self.__known_dates.values():
            # "2022/11/09/2022-11-09.md"
            filename = str(known_date.date) + ".md"
            filepath = "/".join([self.__destination, known_date.date.year, known_date.date.month, filename])
            with create_and_open(filepath, 'a') as file:
                known_date.output(file)

    # Use a dunder overload of getitem to access groups in either way
    # 1. my_librarian["2022-10-10"]
    # 2. my_librarian.access_date("2022-10-10")
    def __getitem__(self, item: str) -> DatedEntriesGroup:
        ref = self.access_date(item)
        return ref

    @property
    def current_mood_set(self):
        return self.__mood_set
