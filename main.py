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

TAGS = "daily, scribbles"
HOW_PARAMETERS_ARE_DELIMITED_IN_DAYLIO_EXPORT_CSV = "," # TODO: not used anymore, delete
HOW_ACTIVITIES_ARE_DELIMITED_IN_DAYLIO_EXPORT_CSV = " | "
NOTE_TITLE_PREFIX = "" # <here's your prefix> YYYY-MM-DD.md
NOTE_TITLE_SUFFIX = "" # YYYY-MM-DD <here's your suffix>.md
HEADER_LEVEL_FOR_INDIVIDUAL_ENTRIES = "##" # H1 headings aren't used because Obsidian introduced automatic inline titles anyway
DO_YOU_WANT_YOUR_ACTIVITIES_AS_TAGS_IN_OBSIDIAN = True

# ------------------------------
from slugify import slugify
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

    @staticmethod
    def sliceQm(str):
        # all strings are enclosed by Daylio with "" inside a CSV. This function strips the string's starting and final quotation marks.
        if len(str) > 2: return str.strip("\"")
        else: return "" # if there are only 2 characters then it MUST be an empty """ cell. Daylio uses a pair of quotations "" for all strings in CSV. If so, let's delete those quotations and return an actual empty string.

# PARSING THE CSV
# ------------------------------
import csv

with open('./daylio.csv', newline='', encoding='UTF-8') as daylioRawImport:
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

for day in days:
    with open('./' + NOTE_TITLE_PREFIX + str(day) + NOTE_TITLE_SUFFIX + '.md', 'w', encoding='UTF-8') as file:
        file.write("---\ntags: " + TAGS + "\n---\n\n")
        
        # Repeat this for every entry written on this day
        for entry in days[day]:

            # compose the title
            thisEntryTitle = entry.mood + " | " + entry.time + " | " + entry.title
            file.write(HEADER_LEVEL_FOR_INDIVIDUAL_ENTRIES + " " + thisEntryTitle)

            # compose the mood-tag and the activity-tags into one paragraph
            file.write("\nI felt #" + slugify(entry.mood))
            if len(entry.activities) > 0 and entry.activities[0] != "":
                file.write(" with the following: ")
                ## first append # to each activity, then mush them together into one string 
                file.write(reduce(lambda el1,el2 : el1+" "+el2, map(lambda x:"#"+x,entry.activities)))
            else: file.write(".")
            
            ## then add the text
            if entry.note != "": file.write("\n" + entry.note + "\n\n")
            else: file.write("\n\n")