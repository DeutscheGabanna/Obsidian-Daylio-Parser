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
import typing
import logging
import datetime
from typing import IO

from daylio_to_md import utils, errors, group
from daylio_to_md.entry.mood import Moodverse
from daylio_to_md.group import EntriesFrom, EntriesFromBuilder
from daylio_to_md.journal_entry import EntryBuilder
from daylio_to_md.utils import CsvLoader, JsonLoader, CouldNotLoadFileError, guess_date_type


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
    CSV_ALL_FIELDS_PRESENT = "All expected columns are present in the CSV file columns."
    CSV_FIELDS_MISSING = "The following expected columns are missing: {}"
    COUNT_ROWS = "{} rows of data found in {}. Of that {} were processed correctly."


class MissingValuesInRowError(utils.ExpectedValueError):
    """The row does not have enough cells - {} needed, {} available."""

    def __init__(self, cells_expected, cells_got):
        super().__init__(cells_expected, cells_got)


class CannotAccessJournalError(utils.CouldNotLoadFileError):
    """The journal .csv {} could not be accessed or parsed."""

    def __init__(self, path: str):
        super().__init__(path)


class EmptyJournalError(utils.CouldNotLoadFileError):
    """The journal .csv {} did not produce any valid journal entries."""

    def __init__(self, path: str):
        super().__init__(path)


class CannotAccessCustomMoodsError(utils.CouldNotLoadFileError):
    """The custom moods .json {} could not be accessed or parsed."""

    def __init__(self, path: str):
        super().__init__(path)


class InvalidDataInFileError(utils.ExpectedValueError):
    """The file does not follow the expected structure."""

    def __init__(self, expected_value, actual_value):
        super().__init__(expected_value, actual_value)


"""---------------------------------------------------------------------------------------------------------------------
MAIN
---------------------------------------------------------------------------------------------------------------------"""


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

    How to process the CSV
    ----------------------
    User only needs to instantiate this object and pass the appropriate arguments.
    The processing does not require invoking any other functions. Functions of this class are therefore mostly private.

    How to output the journal
    -------------------------
    TODO: add missing documentation
    """

    def __init__(self,
                 path_to_file: str,
                 path_to_output: str = None,
                 path_to_moods: str = None,
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
        self.__known_dates: dict[datetime.date, EntriesFrom] = {}
        self.__entries_from_builder = entries_from_builder
        self.__entry_builder = entry_builder

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
        self.__mood_set = self.__create_mood_set(path_to_moods)

        # 2. Access the CSV file and get all the rows with content
        #    then pass the data to specialised data objects that can handle them in a structured way
        try:
            if self.__process_file(path_to_file)[0] == 0:
                raise EmptyJournalError(path_to_file)
        except (CouldNotLoadFileError, InvalidDataInFileError) as err:
            raise CannotAccessJournalError(path_to_file) from err

        # Ok, if no exceptions were raised so far, the file is good, let's go through the rest of the attributes
        self.__destination = path_to_output

    # TODO: this method might actually make more sense as a constructor for Moodverse (give optional arg for custom)
    def __create_mood_set(self, filepath: str = None) -> 'Moodverse':
        """
        Overwrite the standard mood-set with a custom one. Mood-sets are used in colour-coding each dated entry.

        :param filepath: path to the .JSON file with a non-standard mood set.
         Should have five keys: ``rad``, ``good``, ``neutral``, ``bad`` and ``awful``.
         Each of those keys should hold an array of any number of strings indicating various moods.
         **Example**: ``[{"good": ["good"]},...]``
        :returns: reference to the :class:`Moodverse` object
        """
        try:
            with JsonLoader().load(filepath) as file:
                return Moodverse(file)
        except utils.CouldNotLoadFileError:
            # oh, no! anyway... just load up a default moodverse then
            return Moodverse()

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
        # If any ValueError Exception is re-raised up to this method, just exit immediately - no point going further
        try:
            with CsvLoader().load(filepath) as file:
                # TODO: move validation into CsvLoader maybe
                # If the code reaches here, the program can access the file.
                # Now let's determine if the file's contents are actually usable
                # ---

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
                missing_strings = [
                    expected_field for expected_field in expected_fields if
                    expected_field not in file.fieldnames
                ]
                if not missing_strings:
                    self.__logger.debug(ErrorMsg.CSV_ALL_FIELDS_PRESENT)
                else:
                    msg = ErrorMsg.CSV_FIELDS_MISSING.format(', '.join(missing_strings))
                    self.__logger.critical(msg)
                    raise InvalidDataInFileError(file.fieldnames, msg)

                # Processing
                # ---
                lines_parsed = 0
                lines_parsed_successfully = 0
                for line in file:
                    line: dict[str, str]
                    try:
                        lines_parsed += self.__process_line(line)
                    except MissingValuesInRowError as err:
                        self.__logger.warning(err.__doc__)
                    else:
                        lines_parsed_successfully += 1
        except ValueError as err:
            raise CannotAccessJournalError(filepath) from err

        # Report back how many lines were parsed successfully out of all tried
        self.__logger.info(ErrorMsg.COUNT_ROWS.format(lines_parsed, filepath, lines_parsed_successfully))
        return lines_parsed_successfully, lines_parsed

    # TODO: I guess it is more pythonic to raise exceptions than return False if I cannot complete the task
    # TODO: this has to be tested
    # https://eli.thegreenplace.net/2008/08/21/robust-exception-handling/
    def __process_line(self, line: dict[str, str]) -> bool:
        """
        Goes row-by-row and passes the content to objects specialised in handling it from a journaling perspective.
        :param line: a dictionary with values from the currently processed CSV line
        :return: True if all columns had values for this CSV ``line``, False otherwise
        :raises MissingValuesInRowError: if the row in CSV lacks enough commas to create 8 cells. It signals a problem.
        """
        # noinspection PyPep8Naming
        EXPECTED_NUM_OF_CELLS = 8
        # Does each of the 8 columns have values for this row?
        if len(line) < EXPECTED_NUM_OF_CELLS:
            # Oops, not enough values on this row, the file might be corrupted?
            raise MissingValuesInRowError(EXPECTED_NUM_OF_CELLS, len(line))

        # Let DatedEntriesGroup handle the rest and increment the counter (True == 1)
        try:
            date = guess_date_type(line["full_date"])
            entries_from_this_date = (self.__entries_from_builder.build(date, self.__mood_set))
            entries_from_this_date.create_entry(line)
            # Overwriting existing keys is not a problem since EntriesFrom.__new__() returns the same object ID when
            # it is initialised with the same date parameter. Also, since we are type-casting date into datetime.date
            # identical dates will always be equal, so the same key-value pair will be returned by the dictionary.
            self[date] = entries_from_this_date
        except (group.TriedCreatingDuplicateDatedEntryError,
                group.IncompleteDataRow,
                utils.InvalidDateError,
                ValueError):
            return False
        return True

    def output_all(self):
        """
        Loops through known dates and calls :class:`DatedEntriesGroup` to output its contents inside the destination.
        :raises NoDestinationSelectedError: when the parent object has been instantiated without a destination set.
        """
        for known_date in self.__known_dates.values():
            # "2022/11/09/2022-11-09.md"
            filename = str(known_date.date) + ".md"
            filepath = "/".join([self.__destination, str(known_date.date.year), str(known_date.date.month), filename])
            # TODO: maybe add the mode option to settings in argparse? write/append
            with create_and_open(filepath, 'w') as file:
                known_date.output(file)

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
    def current_mood_set(self):
        return self.__mood_set
