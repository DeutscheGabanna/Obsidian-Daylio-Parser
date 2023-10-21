"""Parse a Daylio CSV into an Obsidian-compatible .MD file"""
import logging
import re
import os
import csv
import hashlib
import argparse
from functools import reduce

parser = argparse.ArgumentParser(
    prog="Daylio to Obsidian Parser",
    description="Converts Daylio .CSV backup file into Markdown files for Obsidian.",
    epilog="Created by DeutscheGabanna"
)
parser.add_argument(
    "filepath",
    metavar="file",
    type=open,
    help="Specify path to the .CSV file"
)
parser.add_argument(
    "--prefix", # <here's your prefix> YYYY-MM-DD.md
    default='',
    help="Prepends a given string to each entry's header."
)
parser.add_argument(
    "--suffix", # YYYY-MM-DD <here's your suffix>.md
    default='',
    help="Appends a given string at the end of each entry's header."
)
parser.add_argument(
    "--tag_activities", "-a",
    action="store_false",
    help="Tries to convert activities into valid tags.",
    dest="ACTIVITIES_AS_TAGS"
)
parser.add_argument(
    "-colour", "--color",
    action="store_true",
    help="Prepends a colour emoji to each entry depending on mood.",
    dest="colour"
)
parser.add_argument('--version', action='version', version='%(prog)s 2.0')
parser.add_argument(
    "--header",
    type=int,
    default=2,
    help="Headings level for each entry.",
    dest="HEADER_LEVEL"
)
parser.add_argument(
    "--tags",
    help="Tags in the YAML metadata of each note.",
    default="daily",
    dest="TAGS"
)

settings = parser.parse_args()

# ARCHITECTURE
# ------------------------------
# [dict] days:
#        - [key] YYYY-MM-DD (has to be a unique key)
#           - [list]
#               - [obj] entry at HH:MM
#                   - time
#                   - mood
#                   - [list] activities
#                       - eating
#                       - sleeping
#                   - title (Daylio recently started supporting an entry title)
#                   - note (Daylio recently started allowing basic formating like <b> and <li>)
#               - [obj] another entry at HH:MM
#        - [repeat]

# YOUR VARIABLES
# ------------------------------
# So that you don't need to scroll down to find any easily customatizable parts.

DELIMITER_IN_DAYLIO_EXPORT_CSV = " | "
CUSTOM_EXPORT_LOCATION = r""
# MOODS are used to determine colour coding for the particular moods if colour = TRUE
# [0,x] - best, [4,x] - worst
MOODS=[
    [
        "rad",
        "blissful",
        "excited",
        "relieved",
        "lecturing",
        "beyond pleasure"
    ],
    [
        "vaguely good",
        "captivated",
        "appreciated",
        "authoritative",
        "aroused",
        "in awe",
        "very relaxed",
        "laughing",
        "schadenfreunde",
        "grateful",
        "proud",
        "part of a group",
        "relived",
        "hopeful",
        "social",
        "on edge",
        "loving",
        "rested",
        "happy exercise"
    ],
    [
        "vaguely ok",
        "a bit helpless",
        "fatigued",
        "scared",
        "bored",
        "uneasy",
        "amused",
        "focused",
        "relaxed",
        "intrigued",
        "somewhat rested",
        "in a hurry",
        "conflicted",
        "surprised",
        "bit distracted",
        "reflective",
        "indifferent",
        "groggy",
        "cheering up",
        "refreshed"
    ],
    [
        "vaguely bad",
        "helpless",
        "misunderstood",
        "rejected",
        "incompetent",
        "tired",
        "stressed",
        "terrified",
        "very bored",
        "angry",
        "aching",
        "envy",
        "disgusted",
        "lonely",
        "distracted",
        "cold",
        "impatient",
        "hot",
        "cringe",
        "uncomfortable",
        "skimpy",
        "guilty",
        "sexual unease",
        "hungry",
        "disappointed",
        "annoyed",
        "melting brain",
        "pass-aggressive",
        "hurt emotionally"
    ],
    [
        "vaguely awful",
        "hollow",
        "trapped",
        "dying of pain",
        "furious",
        "mortified",
        "worthless",
        "longing",
        "sexually tense",
        "guilt-ridden",
        "lifeless",
        "nauseous",
        "very stressed",
        "overwhelmed",
        "crying",
        "heart-stabbed"
    ]
]

def slugify(text):
    """Simple slugification function"""
    text = str(text).lower()
    text = re.sub(re.compile(r"\s+"), '-', text)      # Replace spaces with -
    text = re.sub(re.compile(r"[^\w\-]+"), '', text)   # Remove all non-word chars
    text = re.sub(re.compile(r"\-\-+"), '-', text)    # Replace multiple - with single -
    text = re.sub(re.compile(r"^-+"), '', text)       # Trim - from start of text
    text = re.sub(re.compile(r"-+$"), '', text)       # Trim - from end of text
    if settings.ACTIVITIES_AS_TAGS:
        if re.match('[0-9]', text):
            logging.warning("You want your activities as tags, but %s is invalid.", text)
    return text

days = {} # dictionary of days

class Entry(object):
    """Journal entry made at a given moment in time, and describing a particular emotional state"""
    def __init__(self, parsed_line, prop_inside_delimiter = DELIMITER_IN_DAYLIO_EXPORT_CSV):
        # expected CSV row structure: full_date,date,weekday,time,mood,activities,note_title,note
        self.time = parsed_line[3]
        self.mood = parsed_line[4]
        self.activities = self.slice_quotes(parsed_line[5]).split(prop_inside_delimiter)
        for index, _ in enumerate(self.activities):
            self.activities[index] = slugify(self.activities[index])
        self.title = self.slice_quotes(parsed_line[6])
        self.note = self.slice_quotes(parsed_line[7])

    @staticmethod # does not process any data within itself, but relates to the object
    def slice_quotes(string):
        """Gets rid of initial and terminating quotation marks inserted by Daylio"""
        if len(string) > 2:
            return string.strip("\"")
        # only 2 characters? Then it is an empty cell.
        return ""

# PARSING THE CSV
# ------------------------------
with open('./_tests/testing_sheet.csv', newline='', encoding='UTF-8') as daylioRawImport:
    daylioImport = csv.reader(daylioRawImport, delimiter=',', quotechar='"')
    days = {}
    next(daylioImport) # skip first line where headers are located
    for row in daylioImport:
        # create an Entry object instance and pass CSV values from this row into it
        currentEntry = Entry(row)

        # Finding keys for specific days and appending corresponding entries
        # None means that this day has not been added to days yet
        if days.get(row[0]) is None:
            entryList = list()
            entryList.append(currentEntry)
            days[row[0]] = entryList
        else:
            its_a_string_trust_me = row[0]
            days[its_a_string_trust_me].append(currentEntry)

# SETTING THE EXPORT DIRECTORY
if CUSTOM_EXPORT_LOCATION:
    save_path = CUSTOM_EXPORT_LOCATION
else:
    save_path = os.path.join(os.path.expanduser('~'), r'Daylio export')

if not os.path.isdir(save_path):
    os.mkdir(save_path)

# POPULATING OBSIDIAN JOURNAL WITH ENTRIES
# ------------------------------
# According to this schema:
# ---
# tags: <your_custom_tags>
# ---
#
# ### <hour> / <title>
# #activity_1 #activity_2 #activity_3
# <your_entry>
#
# [repeat]

def get_colour(data):
    """Prepend appropriate colour for the mood passed in data"""
    group = ""
    if settings.colour:
        mood_colour=["🟣","🟢","🔵","🟠","🔴"] # 0 - best, 4 - worst mood group
        found = False
        try:
            for index, _ in enumerate(MOODS):
                if data in MOODS[index]:
                    group = mood_colour[index] + " "
                    found = True
        except IndexError:
            logging.warning("Index for MOODS out of bounds, skipping.")
        if not found:
            logging.warning("Incorrecly specified colour criteria, skipping.")
    return group
  
def compile_entry_contents(entry):
    """Return a string that is a parsed entry from Daylio CSV as a string"""
    # compose the title with optional mood colouring
    this_entry_title = get_colour(entry.mood) + entry.mood + " - " + entry.time
    returned_contents = settings.HEADER_LEVEL*'#' + " " + this_entry_title

    # compose the mood-tag and the activity-tags into one paragraph
    returned_contents += "\nI felt #" + slugify(entry.mood)
    if len(entry.activities) > 0 and entry.activities[0] != "":
        returned_contents += " with the following: "
        ## first append # to each activity, then mush them together into one string
        returned_contents += reduce(lambda el1,el2 : el1+" "+el2, map(lambda x:"#"+x,entry.activities))
    else: returned_contents += "."

    ## then add the rest of the text
    if entry.note != "":
        returned_contents += "\n" + entry.note + "\n\n"
    else:
        returned_contents += "\n\n"
    return returned_contents

for day in days:
    contents = "---\ntags: " + settings.TAGS + "\n---\n\n"
    for current_entry in days[day]:
        contents += compile_entry_contents(current_entry)

    # Do we have a file for this day already from previous compilations?
    path_to_file = f"{save_path}/{settings.prefix}{day}{settings.suffix}.md"
    if os.path.exists(path_to_file):
        # Check if the file differs in content from the current proposed output
        ## CALCULATE CHECKSUM FOR FILE
        sha256_hash_file = hashlib.sha256()
        with open(path_to_file,"rb") as f:
            for byte_block in iter(lambda: f.read(4096),b""):
                sha256_hash_file.update(byte_block)
        ## CALCULATE CHECKSUM FOR PROPOSED CONTENT
        sha256_hash_proposed = hashlib.sha256()
        contents_for_hash = contents
        for byte_block in iter(lambda: contents_for_hash[:4096].encode('utf-8'), b""):
            sha256_hash_proposed.update(byte_block)
            contents_for_hash = contents_for_hash[4096:]
        # Differs, so we can overwrite if user agrees
        if sha256_hash_file.hexdigest() != sha256_hash_proposed.hexdigest():
            boolean_answer = None # None means user typed neither yes nor no
            while boolean_answer is None:
                answer = input("%s already exists and differs. Overwrite? (y/n) " % path_to_file)
                if str(answer).lower() in ["yes", "y"]:
                    with open(path_to_file, 'w', encoding='UTF-8') as file:
                        boolean_answer = True
                        file.write(contents)
                elif str(answer).lower() in ["no", "n"]:
                    boolean_answer = False
            # User does not want it to be overwritten
            if boolean_answer is False: 
                continue
        # Does not differ, so we can skip this day
        else: continue
    else:
        with open(path_to_file, 'w', encoding='UTF-8') as file:
            file.write(contents)