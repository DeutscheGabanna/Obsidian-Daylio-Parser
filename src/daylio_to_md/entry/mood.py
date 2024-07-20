from __future__ import annotations

import logging
from typing import List

from daylio_to_md import errors

DEFAULT_DAYLIO_MOOD_GROUPS = "rad good neutral bad awful"


class ErrorMsg(errors.ErrorMsgBase):
    STANDARD_MOODS_USED = "Problem parsing custom moods file. Standard mood set - i.e. {} - will be used."


class MoodNotFoundError(KeyError):
    """The mood could not be found neither in the standard mood set nor the custom one."""
    def __init__(self, key: str):
        super().__init__(key)


# noinspection SpellCheckingInspection
class Moodverse:
    """
    It is the single source of truth regarding moods in a ``dict[str, str]`` format. Keys are moods.
    Values are mood groups to which this particular mood belongs to. It is used to colour them accordingly.

    Basic moodverse
    ---------------
    The most basic instatiation of ``Moodverse()`` with no additional arguments is as follows::

        {"rad": "rad",
        "good": "good",
        "neutral": "neutral",
        "bad": "bad",
        "awful": "awful"}

    Custom moods
    ------------
    Add custom moods by passing a ``dict[str, List[str]]`` in init. Here, keys are mood groups & lists consist of moods.
    Object tries to load as many non-duplicates moods. However, it only looks up moods from keys it knows:
    rad, good, neutral, bad and awful. Other keys are skipped.
    Therefore, it is impossible (or at least should be impossible) to add custom keys. Otherwise, the dictionary
    would become non-compliant with Daylio standards.

    Mood groups
    -----------
    Mood group is an abstract way of thinking about moods, based on categorising them into different groups (or levels).

        *For example*:
        Feeling 'awesome' and 'amazing' all belong to the same group.
        Therefore, if we categorise moods to different categories, we create mood groups.
        They could, for example, range from 5 (best) to 1 (worst).

    :param dict[str, List[str]] moods_to_process: data structure with moods to be added onto the default ones.
    :raise MoodNotFoundError: when trying to access an unknown mood.
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
        self.__known_moods = {mood: mood for mood in DEFAULT_DAYLIO_MOOD_GROUPS.split()}
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

        What moods are skipped
        ----------------------
        Dict keys present in the custom moodset but not present in the standard Daylio moodset are totally ignored.
        Empty strings or non-string values in the List are ignored as well.

        Why keys are moods and values are groups?
        -----------------------------------------
        In case you were wondering why I switched the logical ordering of the dictionary.
        The mood groups used to be keys in the input arg, now they are values.
        Moods, in turn, were turned from a List into keys.
        The logic behind it is that the reverse ordering lends itself better to actual practical usage of the moods.
        When you want to colour a specific mood, you need to find its group colour.
        Therefore, it's easy and ``O(n)`` to do ``dict[mood_name]`` and match it to a particular colour.
        If we keep mood groups as keys, then we would need a dedicated method of finding a mood inside several mood
        groups, and only then would we know which colour to use.

        :param moods_to_process: ``dict[str, List[str]]`` where keys are mood groups and lists contain specific moods.
        :return: ``dict[str, str]`` where key is the name of the mood, and the value is the group it belongs to.
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
        for group in DEFAULT_DAYLIO_MOOD_GROUPS.split():
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
                for mood in sanitised_moods:
                    self.__known_moods[mood] = group
                    custom_moods_found[mood] = group
            except KeyError:
                pass

        # TODO: disallow duplicates in different mod groups - what colour to use if a mood is in more than one grup?
        return custom_moods_found

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self.__known_moods)

    def __eq__(self, other) -> bool:
        if isinstance(other, Moodverse):
            return self.__known_moods == other.get_moods

    def __getitem__(self, item: str) -> str:
        """
        :param item: key to access
        :return: the name of the **group** the mood belongs to, from the list of known moods of this :class:`Moodverse`.
        """
        try:
            return self.__known_moods[item]
        except KeyError:
            raise MoodNotFoundError(item)

    @property
    def get_custom_moods(self) -> dict[str, str]:
        """
        Get the dictionary of only the custom moods known to this instance of :class:`Moodverse`.
        :return: ``dict[str, str]`` where keys are moods and their values are mood groups they belong to
        """
        return self.__custom_moods

    @property
    def get_moods(self) -> dict[str, str]:
        """
        Get the dictionary of all moods known to this instance of :class:`Moodverse`.
        :return: ``dict[str, str]`` where keys are moods and their values are mood groups they belong to
        """
        return self.__known_moods
