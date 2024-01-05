"""
Librarian is a builder/singleton type class. It creates and initialises other builder objects - e.g. DatedEntriesGroup.
It sets up the process, parses the CSV file and passes extracted values to DatedEntriesGroup.
Imagine Librarian is an actual person, reading the contents of the file out-loud to a scribe (DatedEntriesGroup).
Each date is a different scribe, but they all listen to the same Librarian.
Librarian knows their identity and can call upon them when needed to recite their contents back to the Librarian.

Here's a quick breakdown of what is the specialisation of this file in the journaling process:
└── ALL NOTES
    └── notes written on a particular date
        └── a particular note
"""
import csv
import json
import logging
import sys
from typing import List

from config import options
import errors
import utils
from dated_entries_group import DatedEntriesGroup

# Adding Librarian-specific options in global_settings
librarian_settings = options.get_console().add_argument_group(
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
    CSV_FIELDS_MISSING = "The following expected columns are missing: "
    COUNT_ROWS = "Found {} rows of data in {}."


# Here's a quick reference what a "minimal viable" JSON there needs to be if you want to have custom mood-sets.
# If you do not pass a custom one, the application uses the following structure as a fallback mood-set.
standard_mood_set = {
    "rad": ["rad"],
    "good": ["good"],
    "neutral": ["neutral"],
    "bad": ["bad"],
    "awful": ["awful"]
}


class MissingValuesInRowError(utils.CustomException):
    """If a CSV row does not have enough values needed to create an entry."""


class CannotAccessFileError(utils.CustomException):
    """The file could not be accessed."""


class InvalidDataInFileError(utils.CustomException):
    """The file does not follow the expected structure."""


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
                 path_to_output: str = None,  # TODO: `None` should block any outputting functions
                 path_to_moods: str = None):
        """
        :param path_to_file: The path to the CSV file for processing.
        :param path_to_output: The path for outputting processed data as markdown files.
         If user does not provide the output path, no output functionality will work.
        :raises CannotAccessFileError: if any problems occur during accessing or decoding the CSV file.
        :param path_to_moods: The path for a custom mood set file.
        """

        self.__known_moods = standard_mood_set
        self.__known_dates = {}
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__destination = path_to_output

        # Let's start processing the file
        # ---
        # 1. Parse the path_to_moods JSON to see if a custom mood-set has to be used
        if path_to_moods is not None:
            try:
                self.__set_custom_moods(path_to_moods)
            except CannotAccessFileError:
                pass

        # 2. Access the CSV file and get all the rows with content
        #    then pass the data to specialised data objects that can handle them in a structured way
        try:
            self.__process_file(path_to_file)
        except CannotAccessFileError:
            raise CannotAccessFileError

    @property
    def custom_moods(self) -> dict[str, List[str]] | None:
        """
        :returns: dictionary of rad, good, neutral, bad and awful moods that this Librarian instance knows about
        """
        if self.__known_moods != standard_mood_set:
            return self.__known_moods
        else:
            return None

    def __set_custom_moods(self, json_file: str):
        """
        Overwrite the standard mood-set with a custom one. Mood-sets are used in colour-coding each dated entry.

        :param json_file: path to the .JSON file with a non-standard mood set.
         Should have five keys: ``rad``, ``good``, ``neutral``, ``bad`` and ``awful``.
         Each of those keys should hold an array of any number of strings indicating various moods.
         **Example**: ``[{"good": ["good"]},...]``
        :raises CannotAccessFileError: if any problems occur during accessing or decoding the JSON.
        :returns: success or failure to set
        """
        exp_path = utils.expand_path(json_file)
        try:
            with open(exp_path, encoding="UTF-8") as file:
                tmp_mood_set = json.load(file)
        except FileNotFoundError:
            msg = ErrorMsg.print(ErrorMsg.FILE_MISSING, exp_path)
            self.__logger.warning(msg)
            raise CannotAccessFileError(msg)
        except PermissionError:
            msg = ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, exp_path)
            self.__logger.warning(msg)
            raise CannotAccessFileError(msg)
        except json.JSONDecodeError:
            msg = ErrorMsg.print(ErrorMsg.DECODE_ERROR, exp_path)
            self.__logger.warning(msg)
            raise CannotAccessFileError(msg)

        # Try accessing each mood key to watch for KeyError if missing
        for mood_key in self.__known_moods.keys():
            try:
                tmp_mood_set[mood_key]
            except KeyError:
                msg = ErrorMsg.print(ErrorMsg.FILE_INCOMPLETE, exp_path)
                self.__logger.warning(msg)
                raise InvalidDataInFileError(msg)
            else:
                continue

        # At this point, we know each mood key is present so the dictionary is valid
        self.__known_moods = tmp_mood_set

    def __process_file(self, filepath: str) -> bool:
        """
        Validates CSV file and processes it into iterable rows.

        :param filepath: path to CSV to be read
        :raises CannotAccessFileError: if any problems occur during accessing or decoding the CSV file.
        :returns: True if parsed > 0, False otherwise
        """
        if not self.custom_moods:
            self.__logger.info(ErrorMsg.print(ErrorMsg.STANDARD_MOODS_USED))

        # Let's determine if the file can be opened
        # ---
        try:
            file = open(filepath, newline='', encoding='UTF-8')
        # File has not been found
        except FileNotFoundError:
            msg = ErrorMsg.print(ErrorMsg.FILE_MISSING, filepath)
            self.__logger.critical(msg)
            raise CannotAccessFileError(msg)
        # Insufficient permissions to access the file
        except PermissionError:
            msg = ErrorMsg.print(ErrorMsg.PERMISSION_ERROR, filepath)
            self.__logger.critical(msg)
            raise CannotAccessFileError(msg)
        # Other error that makes it impossible to access the file
        except OSError:
            self.__logger.critical(OSError)
            raise CannotAccessFileError

        # If the code reaches here, the program can access the file.
        # Now let's determine if the file's contents are actually usable
        # ---

        with file:
            # Is it a valid CSV?
            try:
                # strict parameter throws csv.Error if parsing fails
                # if the parsing fails, exit immediately
                raw_lines = csv.DictReader(file, delimiter=',', quotechar='"', strict=True)
            except csv.Error:
                msg = ErrorMsg.print(ErrorMsg.DECODE_ERROR, filepath)
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg)

            # Does it have all the fields? Push any missing field into an array for later reference
            # Even if only one column from the list below is missing in the CSV, exit immediately
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
            missing_strings = [expected_field for expected_field in expected_fields if
                               expected_field not in raw_lines.fieldnames]

            if not missing_strings:
                self.__logger.debug(ErrorMsg.print(ErrorMsg.CSV_ALL_FIELDS_PRESENT))
            else:
                msg = ErrorMsg.print(
                        ErrorMsg.CSV_FIELDS_MISSING,
                        ', '.join(missing_strings)  # which ones are missing - e.g. "date, mood, note"
                )
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg)

            # Does it have any rows besides the header?
            # If the file is empty or only has column headers, exit immediately
            try:
                next(raw_lines)
            except StopIteration:
                msg = ErrorMsg.print(ErrorMsg.FILE_EMPTY, filepath)
                self.__logger.critical(msg)
                raise InvalidDataInFileError(msg)

            # If the code has reached this point and has not exited, it means both file and contents have to be ok
            # Processing
            # ---
            lines_parsed = 0
            for line in raw_lines:
                line: dict[str]
                try:
                    lines_parsed += self.__process_line(line)
                except MissingValuesInRowError:
                    pass

            self.__logger.info(ErrorMsg.print(ErrorMsg.COUNT_ROWS, str(lines_parsed), filepath))

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
        else:
            # Let DatedEntriesGroup handle the rest and increment the counter (True == 1)
            try:
                self.access_date(line["full_date"]).create_dated_entry_from_row(line, known_moods=self.__known_moods)
            except:
                return False
            else:
                return True

    def access_date(self, target_date: str) -> DatedEntriesGroup:
        """
        Accesses an already existing or creates a new :class:`DatedEntriesGroup` for the specified ``target_date``.
        :param target_date: the date for which a unique :class:`DatedEntriesGroup` object should be created or accessed.
        :return: reference to :class:`DatedEntriesGroup` object
        """
        date_obj = DatedEntriesGroup(target_date)

        # have you already filed this date?
        # TODO: maybe I should use a Date object instead of a string for comparison in the dict?
        if target_date in self.__known_dates:
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_FOUND, target_date))
        else:
            self.__logger.debug(ErrorMsg.print(ErrorMsg.OBJECT_NOT_FOUND, target_date))
            self.__known_dates[date_obj.uid] = date_obj

        return date_obj
