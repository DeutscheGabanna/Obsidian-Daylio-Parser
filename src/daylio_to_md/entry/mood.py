from __future__ import annotations

import logging
from typing import List

from daylio_to_md import utils, errors

DEFAULT_DAYLIO_MOODGROUPS = "rad good neutral bad awful"


class ErrorMsg(errors.ErrorMsgBase):
    MOOD_GROUP_NOT_FOUND = "Expected to find {} mood group, but the key is missing from the dictionary."
    STANDARD_MOODS_USED = "Problem parsing custom moods file. Standard mood set - i.e. {} - will be used."
    SKIPPED_INVALID_MOOD = "Skipping \'{}\' as it is not a valid mood."


class EmptyValue(utils.CustomException):
    """Attribute cannot be set to empty."""


class MoodNotFoundError(utils.CustomException):
    """The mood could not be found neither in the standard mood set nor the custom one."""


# noinspection SpellCheckingInspection
class Moodverse:
    """
    Moodverse is the single source of truth regarding moods in a dict[str, str] format.
    The most basic instatiation of Moodverse is as follows::

        {"rad": "rad",
        "good": "good",
        "neutral": "neutral",
        "bad": "bad",
        "awful": "awful"}

    This can be expanded by providing more moods during initalisation. Object tries to load as many non-duplicates.
    However, it only looks up moods from keys that it knows - rad, good, neutral, bad and awful. Other keys are skipped.

    :param dict[str, List[str]] moods_to_process: data structure with moods to be added onto the default ones

    Mood group is an abstract way of thinking about moods, based on categorising them into different groups (or levels).

    For example:
    Feeling 'awesome' and 'amazing' all belong to the same group.
    Therefore, if we categorise moods to different categories, we create mood groups.
    They could, for example, range from 5 (best) to 1 (worst).

    :raises MoodNotFoundError:
    """
    __slots__ = ('__known_moods', '__logger', '__custom_moods')
    __known_moods: dict[str, str]
    __custom_moods: dict[str, str]

    def __init__(self, moods_to_process: dict[str, List[str]] = None):
        self.__logger = logging.getLogger(self.__class__.__name__)

        # DEFAULT PART OF INIT
        # --------------------
        # Build a minimal-viable mood set with these five mood groups
        # .
        # ├── known moods of 'rad' group
        # │   └── rad
        # ├── known moods of 'great' group
        # │   └── great
        # ├── known moods of 'neutral' group
        # │   └── neutral
        # ├── known moods of 'bad' group
        # │   └── bad
        # └── known moods of 'awful' group
        #     └── awful

        # I know this line is shitty, but I don't have access to const or immutable lists, so I rely on str.strip()
        # When I tried using mutable dicts or lists, the problem was that something in my code kept overwriting it
        self.__known_moods = {mood: mood for mood in DEFAULT_DAYLIO_MOODGROUPS.split()}
        self.__custom_moods = {}

        # We can stop here and be content with our "default" / "standard" mood-set if user did not pass a custom one
        # CUSTOM PART OF INIT
        # --------------------
        if moods_to_process is not None:
            try:
                self.__custom_moods = self.__expand_moodset_with_customs(moods_to_process)
            except MoodNotFoundError:
                msg = ErrorMsg.print(ErrorMsg.STANDARD_MOODS_USED, ', '.join(str(item) for item in self.__known_moods))
                self.__logger.warning(msg)

    def __expand_moodset_with_customs(self, moods_to_process: dict[str, List[str]]) -> dict[str, str]:
        """
        Expands the knowledge of this specific :class:`Moodverse` with new custom moods passed by user.
        Dict keys present in the custom moodset but not present in the standard Daylio moodset are totally ignored.
        Empty strings or non-string values in the List are ignored as well.
        :param moods_to_process: Lists of str moods grouped into five dictionary keys: rad, great, neutral, bad & awful
        :returns: `True` if successfully expanded moodset, `False` otherwise
        """
        # Then expand the minimal-viable mood set from Moodverse __init__
        # .
        # ├── known moods of 'rad' group
        # │   └── rad
        # │   └── (add more...)
        # ├── known moods of 'great' group
        # │   └── great
        # │   └── (add more...)
        # ├── known moods of 'neutral' group
        # │   └── neutral
        # │   └── (add more...)
        # ├── known moods of 'bad' group
        # │   └── bad
        # │   └── (add more...)
        # └── known moods of 'awful' group
        #     └── awful
        #     └── (add more...)
        custom_moods_found = {}
        # By itering on the dictionary of known mood groups (which are always Daylio-compliant), we skip unknown groups.
        # Unknown moods are OK, but they need to be within a known GROUP.
        for group in DEFAULT_DAYLIO_MOODGROUPS.split():
            # Set:
            # - gets rid of duplicates
            # - ignores values already in the known mood dict
            # - ignores non-strings or empty strings
            try:
                sanitised_moods = set(
                    mood
                    for mood in moods_to_process[group]
                    if isinstance(mood, str) and mood and mood not in self.__known_moods
                )
            except KeyError:
                sanitised_moods = set()

            # TODO: test this
            for mood in sanitised_moods:
                self.__known_moods[mood] = group
                custom_moods_found[mood] = group

        # TODO: disallow duplicates in different mod groups - what colour to use if a mood is in more than one grup?
        return custom_moods_found

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.__known_moods)

    def __eq__(self, other):
        if isinstance(other, Moodverse):
            return self.__known_moods == other.get_moods

    # basically a getter for the self.__known_moods var - like so: obj["rad"]
    def __getitem__(self, item: str):
        try:
            return self.__known_moods[item]
        except KeyError:
            raise MoodNotFoundError

    @property
    def get_custom_moods(self) -> dict[str, str]:
        return self.__custom_moods

    @property
    def get_moods(self) -> dict[str, str]:
        return self.__known_moods

