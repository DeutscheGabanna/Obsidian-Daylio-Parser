"""COMPILE STRUCTURED DATA INTO STRING TO OUTPUT
---------------------------------------------
According to this schema:
---
tags: <your_custom_tags>
---

### <hour> / <title>
#activity_1 #activity_2 #activity_3
<your_entry>

[repeat]
"""
import logging
from functools import reduce
# Other
from cmd_args import settings
import load_moods
import utils

def compile_note_yaml():
    """Returns string with YAML metadata for each note. It looks like this:
    ---
    tags: <your_custom_tags>
    ---
    """
    return f"---\ntags: {settings.TAGS} \n---\n\n"

def compile_entry_contents(entry):
    """Return a string that is a parsed entry from Daylio CSV as a string.
    It looks like this:
    
    ### <hour> / <title>
    #activity_1 #activity_2 #activity_3
    <your_entry>
    
    """
    # compose the title with optional mood colouring
    this_entry_title = get_colour(entry.mood) + entry.mood + " - " + entry.time
    final_output = settings.HEADER_LEVEL*'#' + " " + this_entry_title

    # compose the mood-tag and the activity-tags into one paragraph
    final_output += "\nI felt #"
    final_output += utils.slugify(entry.mood, settings.ACTIVITIES_AS_TAGS)
    if len(entry.activities) > 0 and entry.activities[0] != "":
        final_output += " with the following: "
        ## first append # to each activity, then mush them together into one string
        final_output += reduce(
            lambda el1,el2 : el1+" "+el2, map(lambda x:"#"+x,entry.activities)
        )
    else: final_output += "."

    ## then add the rest of the text
    if entry.note != "":
        final_output += "\n" + entry.note + "\n\n"
    else:
        final_output += "\n\n"
    return final_output

def get_colour(mood_to_check):
    """Prepend appropriate colour for the mood passed in mood_to_check"""
    prepended_colour = ""
    mood_colour=["🟣","🟢","🔵","🟠","🔴"] # 0 - best, 4 - worst mood group
    if settings.colour:
        for i, (_, this_group) in enumerate(load_moods.available_moods.items()):
            if mood_to_check in this_group:
                prepended_colour = f"{mood_colour[i]} "
        if not prepended_colour:
            logging.warning("%s was not found in moods.json database.", mood_to_check)
    return prepended_colour
