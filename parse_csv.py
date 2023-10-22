"""Creates structured data from Daylio .CSV"""
import csv
import utils
import cmd_args

delimiter = f" {cmd_args.settings.csv_delimiter} "

class Entry:
    """Journal entry made at a given moment in time, and describing a particular emotional state"""
    def __init__(self, parsed_line, prop_inside_delimiter = delimiter):
        # expected CSV row structure: full_date,date,weekday,time,mood,activities,note_title,note
        # TODO: incomplete CSV support
        self.time = parsed_line[3]
        self.mood = parsed_line[4]
        self.activities = self.slice_quotes(parsed_line[5]).split(prop_inside_delimiter)
        for index, _ in enumerate(self.activities):
            self.activities[index] = utils.slugify(
                self.activities[index],
                cmd_args.settings.ACTIVITIES_AS_TAGS
            )
        self.title = self.slice_quotes(parsed_line[6])
        self.note = self.slice_quotes(parsed_line[7])

    @staticmethod # does not process any mood_to_check within itself, but relates to the object
    def slice_quotes(string):
        """Gets rid of initial and terminating quotation marks inserted by Daylio"""
        if len(string) > 2:
            return string.strip("\"")
        # only 2 characters? Then it is an empty cell.
        return ""

def setup(path):
    """Open .CSV file in the path and populate array of Entries"""
    with open(path, newline='', encoding='UTF-8') as daylio_raw:
        daylio_raw_line = csv.reader(daylio_raw, delimiter=',', quotechar='"')
        days = {}
        next(daylio_raw_line) # only headers in first line, skip
        for row in daylio_raw_line:
            # create an Entry object instance and pass CSV values from this row into it
            current_entry = Entry(row)

            # Finding keys for specific days and appending corresponding entries
            # None means that this day has not been added to days yet
            if days.get(row[0]) is None:
                entry_list = []
                entry_list.append(current_entry)
                days[row[0]] = entry_list
            else:
                its_a_string_trust_me = row[0]
                days[its_a_string_trust_me].append(current_entry)
        return days
