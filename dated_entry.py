"""Creates structured data from Daylio .CSV"""
import logging
import re

import errors
import utils


def is_time_format_valid(string):
    return re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]($|\sAM|\sPM)').match(string)


def is_time_range_valid(string):
    time_array = string.strip().split(':')

    # Check if it's in 12-hour format (AM/PM) or 24-hour format
    if 'AM' in string or 'PM' in string:
        is_hour_ok = 0 <= int(time_array[0]) <= 12
    else:
        is_hour_ok = 0 <= int(time_array[0]) < 24

    # Minutes can be checked irrespective of AM/PM/_ notation
    is_minutes_ok = 0 <= int(time_array[1][:2]) < 60

    return all((is_hour_ok, is_minutes_ok))


def slice_quotes(string):
    """
    Gets rid of initial and terminating quotation marks inserted by Daylio
    """
    if len(string) > 2:
        return string.strip("\"")
    # only 2 characters? Then it is an empty cell.
    return ""


class ErrorMsg(errors.ErrorMsgBase):
    INVALID_MOOD = "Mood {} is missing from a list of known moods. Colouring won't work for this one."
    WRONG_PARENT = "Object of class {} is trying to instantiate {} as child. This will end badly."


class Time:
    """
    Hour and minutes of a particular moment in time. Validates the time string on instantiation.
    str(instance) returns the valid time in the HH:MM format.
    """

    def __init__(self, string):
        self.__logger = logging.getLogger(self.__class__.__name__)

        if is_time_format_valid(string) and is_time_range_valid(string):
            time_array = string.strip().split(':')
            self.__hour = time_array[0]
            self.__minutes = time_array[1]
        else:
            msg_on_error = ErrorMsg.print(ErrorMsg.WRONG_VALUE, string, "HH:MM (AM/PM/)")
            self.__logger.warning(msg_on_error)
            raise ValueError(msg_on_error)

    def __str__(self):
        return ':'.join([self.__hour, self.__minutes])


class DatedEntry(utils.Core):
    """
    Journal entry made at a given moment in time, and describing a particular emotional state.
    It inherits None uid from utils.Core which is then set to self.time. Object is unusable without uid.
    """

    def __init__(self,
                 time,
                 parent,
                 mood,
                 known_moods):
        self.__logger = logging.getLogger(self.__class__.__name__)
        super().__init__()

        self.set_uid(Time(time))

        self.__mood = self.set_mood(mood, known_moods)
        self.__activities = []
        self.__title = None
        self.__note = None
        self.__parent = parent

    def __bool__(self):
        # A DatedEntry is truthy only if it contains a healthy parent, time/uid and mood
        return all([
            super().__bool__(),
            self.get_uid(),
            self.get_mood(),
            self.get_parent()
        ])

    def set_mood(self, mood, list_of_moods):
        valid = False
        for i, (_, this_group) in enumerate(list_of_moods.items()):
            if mood in this_group:
                valid = True
        if not valid:
            self.__logger.warning(ErrorMsg.print(ErrorMsg.INVALID_MOOD, mood))
        # Assign it anyway. Warning is enough.
        self.__mood = mood
        return True

    def get_mood(self):
        return self.__mood

    def set_activities(self, pipe_delimited_activity_string, delimiter, should_taggify):
        array = slice_quotes(pipe_delimited_activity_string).split(delimiter)
        if len(array) > 0:
            for activity in array:
                self.__activities.append(utils.slugify(
                    activity,
                    should_taggify
                ))
            return True
        else:
            return False

    def get_activities(self):
        return self.__activities

    def set_title(self, title):
        if len(title) > 0:
            self.__title = slice_quotes(title)
            return True
        else:
            return False

    def get_title(self):
        return self.__title

    def set_note(self, note):
        if len(note) > 0:
            self.__note = slice_quotes(note)
            return True
        else:
            return False

    def get_note(self):
        return self.__note

    def get_parent(self):
        return self.__parent
