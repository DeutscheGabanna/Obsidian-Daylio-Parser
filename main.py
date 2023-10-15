import logging

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

TAGS = "daily"
HOW_ACTIVITIES_ARE_DELIMITED_IN_DAYLIO_EXPORT_CSV = " | "
NOTE_TITLE_PREFIX = "" # <here's your prefix> YYYY-MM-DD.md
NOTE_TITLE_SUFFIX = "" # YYYY-MM-DD <here's your suffix>.md
HEADER_LEVEL_FOR_INDIVIDUAL_ENTRIES = "##" # H1 headings aren't used because Obsidian introduced automatic inline titles anyway
DO_YOU_WANT_YOUR_ACTIVITIES_AS_TAGS_IN_OBSIDIAN = True
CUSTOM_EXPORT_LOCATION = r""
GET_COLOUR = True
# MOODS are used to determine colour coding for the particular moods if GET_COLOUR = TRUE
# [0,x] - best, [4,x] - worst
MOODS=[
    ["rad", "blissful", "excited", "relieved", "lecturing", "beyond pleasure"],
    ["vaguely good", "captivated", "appreciated", "authoritative", "aroused", "in awe", "very relaxed", "laughing", "schadenfreunde", "grateful", "proud", "part of a group", "relived", "hopeful", "social", "on edge", "loving", "rested", "happy exercise"],
    ["vaguely ok", "a bit helpless", "fatigued", "scared", "bored", "uneasy", "amused", "focused", "relaxed", "intrigued", "somewhat rested", "in a hurry", "conflicted", "surprised", "bit distracted", "reflective", "indifferent", "groggy", "cheering up", "refreshed"],
    ["vaguely bad", "helpless", "misunderstood", "rejected", "incompetent", "tired", "stressed", "terrified", "very bored", "angry", "aching", "envy", "disgusted", "lonely", "distracted", "cold", "impatient", "hot", "cringe", "uncomfortable", "skimpy", "guilty", "sexual unease", "hungry", "disappointed", "annoyed", "melting brain", "pass-aggressive", "hurt emotionally"],
    ["vaguely awful", "hollow", "trapped", "dying of pain", "furious", "mortified", "worthless", "longing", "sexually tense", "guilt-ridden", "lifeless", "nauseous", "very stressed", "overwhelmed", "crying", "heart-stabbed"]
]

# ------------------------------
import re
def slugify(text):
    text = str(text).lower()
    text = re.sub(re.compile(r"\s+"), '-', text)      # Replace spaces with -
    text = re.sub(re.compile(r"[^\w\-]+"), '', text)   # Remove all non-word chars
    text = re.sub(re.compile(r"\-\-+"), '-', text)    # Replace multiple - with single -
    text = re.sub(re.compile(r"^-+"), '', text)       # Trim - from start of text
    text = re.sub(re.compile(r"-+$"), '', text)       # Trim - from end of text
    if (DO_YOU_WANT_YOUR_ACTIVITIES_AS_TAGS_IN_OBSIDIAN):
        if re.match('[0-9]', text):
            logging.warning("You want your activities as tags, but " + text + " is an invalid tag in Obsidian")
    return text
    
import os # On Unix and Windows, return the argument with an initial component of ~ or ~user replaced by that user’s home directory.
days = {} # dictionary of days

class Entry(object):
    def __init__(self, parsedLine, propInsideDelimiter = HOW_ACTIVITIES_ARE_DELIMITED_IN_DAYLIO_EXPORT_CSV): # propInsideDelimiter -> delimiters within CSV cells like "one | two | three", compare with propDelimiter -> key:value,key:value,key:value in typical CSV
        # the expected CSV row structure: full_date,date,weekday,time,mood,activities,note_title,note
        self.time = parsedLine[3]
        self.mood = parsedLine[4]
        self.activities = self.sliceQm(parsedLine[5]).split(propInsideDelimiter) # table of activities
        for index, item in enumerate(self.activities):
            self.activities[index] = slugify(self.activities[index])
        self.title = self.sliceQm(parsedLine[6])
        self.note = self.sliceQm(parsedLine[7])

    @staticmethod # because it doesn't need to process any information within the object itself, but relates to it somehow
    def sliceQm(str):
        # all strings are enclosed by Daylio with "" inside a CSV. This function strips the string's starting and final quotation marks.
        if len(str) > 2: return str.strip("\"")
        else: return "" # if there are only 2 characters then it MUST be an empty """ cell. Daylio uses a pair of quotations "" for all strings in CSV. If so, let's delete those quotations and return an actual empty string.

# PARSING THE CSV
# ------------------------------
import csv

with open('./_tests/testing_sheet.csv', newline='', encoding='UTF-8') as daylioRawImport:
    daylioImport = csv.reader(daylioRawImport, delimiter=',', quotechar='"')
    days = {}
    next(daylioImport) # skip first line where headers are located
    for row in daylioImport:
        currentEntry = Entry(row) # create an Entry object instance and pass CSV values from this row into it

        # Finding keys for specific days and appending corresponding entries 
        if (days.get(row[0]) == None): # None means that this day has not been added to days yet
            entryList = list()
            entryList.append(currentEntry)
            days[row[0]] = entryList
        else:
            its_a_string_trust_me = row[0]
            days[its_a_string_trust_me].append(currentEntry)

# SETTING THE EXPORT DIRECTORY
save_path = CUSTOM_EXPORT_LOCATION if CUSTOM_EXPORT_LOCATION else os.path.join(os.path.expanduser('~'), r'Daylio export') 
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
from functools import reduce
import hashlib # for SHA-256 checksum

def get_colour(data):
    group = ""
    if (GET_COLOUR):
        mood_colour=["🟣","🟢","🔵","🟠","🔴"] # 0 - best, 4 - worst mood group
        found = False
        try:
            for index, item in enumerate(MOODS):
                if data in MOODS[index]:
                    group = mood_colour[index] + " " # return emoji to be prepended for the given entry
                    found = True
        except IndexError:
            logging.warning("Index for MOODS out of bounds, skipping.")
        if not found: logging.warning("Incorrecly specified colour criteria, skipping.")
    return group

def compile_entry_contents(entry):
    # compose the title with optional mood colouring
    thisEntryTitle = get_colour(entry.mood) + entry.mood + " - " + entry.time
    contents = HEADER_LEVEL_FOR_INDIVIDUAL_ENTRIES + " " + thisEntryTitle

    # compose the mood-tag and the activity-tags into one paragraph
    contents += "\nI felt #" + slugify(entry.mood)
    if len(entry.activities) > 0 and entry.activities[0] != "":
        contents += " with the following: "
        ## first append # to each activity, then mush them together into one string 
        contents += reduce(lambda el1,el2 : el1+" "+el2, map(lambda x:"#"+x,entry.activities))
    else: contents += "."
    
    ## then add the rest of the text
    if entry.note != "": contents += "\n" + entry.note + "\n\n"
    else: contents += "\n\n"
    return contents

for day in days:
    contents = "---\ntags: " + TAGS + "\n---\n\n"
    for entry in days[day]:
        contents += compile_entry_contents(entry)

    # Do we have a file for this day already from previous compilations?
    path_to_file = save_path + '/' + NOTE_TITLE_PREFIX + str(day) + NOTE_TITLE_SUFFIX + '.md'
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
        if not sha256_hash_file.hexdigest() == sha256_hash_proposed.hexdigest():
            boolean_answer = None # None means user typed neither yes nor no
            while boolean_answer is None:
                answer = input("File " + path_to_file + " already exists and differs in content. Overwrite? (y/n) ")
                if str(answer).lower() in ["yes", "y"]:
                    with open(path_to_file, 'w', encoding='UTF-8') as file:
                        boolean_answer = True
                        file.write(contents)
                elif str(answer).lower() in ["no", "n"]:
                    boolean_answer = False
            # User does not want it to be overwritten
            if boolean_answer is False: continue
        # Does not differ, so we can skip this day
        else: continue