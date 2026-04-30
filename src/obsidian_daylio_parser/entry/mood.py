from __future__ import annotations

import logging
from dataclasses import dataclass
from os import PathLike
from typing import List

from obsidian_daylio_parser import logs
from obsidian_daylio_parser.logs import logger
from obsidian_daylio_parser.utils import JsonLoader, CouldNotLoadFileError


@dataclass(frozen=True)
class MoodGroup:
    """A Daylio mood group: a named category that carries its own colour emoji."""
    name: str
    colour: str

    def __post_init__(self):
        if len(self.colour) != 1:
            raise ValueError


# TODO: Unfortunately Daylio uses localised strings for mood groups, so these will work only for English exports :(
# Single source of truth for built-in groups. To add a new group, add one entry here — nothing else.
BUILTIN_GROUPS: dict[str, MoodGroup] = {
    "rad":     MoodGroup("rad",     chr(0x1F7E9)),
    "good":    MoodGroup("good",    chr(0x1F7E6)),
    "neutral": MoodGroup("neutral", chr(0x2B1C)),
    "bad":     MoodGroup("bad",     chr(0x1F7E7)),
    "awful":   MoodGroup("awful",   chr(0x1F7E5)),
}


class ErrorMsg(logs.LogMsg):
    STANDARD_MOODS_USED = "Problem parsing custom moods file. Standard mood set - i.e. {} - will be used."


class MoodNotFoundError(KeyError):
    """The mood could not be found neither in the standard mood set nor the custom one."""
    def __init__(self, key: str):
        super().__init__(key)


# noinspection SpellCheckingInspection
class Moodverse:
    """
    It is the single source of truth regarding moods in a ``dict[str, MoodGroup]`` format. Keys are moods.
    Values are :class:`MoodGroup` objects the mood belongs to, carrying the group name and its colour emoji.

    Basic moodverse
    ---------------
    The most basic instantiation of ``Moodverse()`` with no additional arguments seeds itself from
    :data:`BUILTIN_GROUPS`, so each group name is also registered as its own first mood::

        {"rad": MoodGroup("rad", "🟩"),
        "good": MoodGroup("good", "🟦"),
        "neutral": MoodGroup("neutral", "⬜"),
        "bad": MoodGroup("bad", "🟧"),
        "awful": MoodGroup("awful", "🟥")}

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
    __known_moods: dict[str, MoodGroup]
    __custom_moods: dict[str, MoodGroup]

    def __init__(self, moods_to_process: dict[str, List[str]] = None):

        # DEFAULT PART OF INIT
        # --------------------
        # Seed from BUILTIN_GROUPS: each group name is its own first mood.
        # .
        # ├── known moods of 'rad' group
        # │   └── rad → MoodGroup("rad", "🟩")
        # ├── known moods of 'good' group
        # │   └── good → MoodGroup("good", "🟦")
        # ├── known moods of 'neutral' group
        # │   └── neutral → MoodGroup("neutral", "⬜")
        # ├── known moods of 'bad' group
        # │   └── bad → MoodGroup("bad", "🟧")
        # └── known moods of 'awful' group
        #     └── awful → MoodGroup("awful", "🟥")
        self.__known_moods = {name: group for name, group in BUILTIN_GROUPS.items()}
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

    @classmethod
    def from_file(cls, filepath: PathLike = None) -> 'Moodverse':
        """
        Load a custom mood set from a JSON file. Falls back to default moods if the file is missing or invalid.

        :param filepath: path to the ``.json`` file with a non-standard mood set.
            Pass ``None`` to use the default mood set.
        :returns: :class:`Moodverse` instance — custom if the file loaded successfully, default otherwise.
        """
        if filepath is None:
            return cls()
        try:
            with JsonLoader().load(filepath) as data:
                return cls(data)
        except CouldNotLoadFileError:
            logger.warning(
                "Could not load custom moods from %s. Using defaults.", filepath
            )
            return cls()

    def __expand_moodset_with_customs(self, moods_to_process: dict[str, List[str]]) -> dict[str, MoodGroup]:
        """
        Expands the knowledge of this specific :class:`Moodverse` with new custom moods passed by user.

        What moods are skipped
        ----------------------
        Dict keys present in the custom moodset but not present in ``BUILTIN_GROUPS`` are totally ignored.
        Empty strings or non-string values in the List are ignored as well.

        Why keys are moods and values are MoodGroup objects?
        ----------------------------------------------------
        The mood groups used to be keys in the input arg, now they are values.
        Moods, in turn, were turned from a List into keys.
        The logic behind it is that the reverse ordering lends itself better to actual practical usage.
        When you want to colour a specific mood, you need its group's colour.
        Therefore, it's O(1) to do ``dict[mood_name]`` and get a :class:`MoodGroup` carrying both the group
        name and the colour emoji.
        If we kept mood groups as keys, finding a mood would require iterating across several mood groups.

        :param moods_to_process: ``dict[str, List[str]]`` where keys are mood groups and lists contain specific moods.
        :return: ``dict[str, MoodGroup]`` where key is the name of the mood, value is the group it belongs to.
        """
        custom_moods_found = {}
        # By iterating BUILTIN_GROUPS keys we automatically skip any unknown groups from the JSON.
        for group_name, mood_group in BUILTIN_GROUPS.items():
            try:
                sanitised_moods = set(
                    mood
                    for mood in moods_to_process[group_name]
                    if isinstance(mood, str) and mood and mood not in self.__known_moods
                )
                for mood in sanitised_moods:
                    self.__known_moods[mood] = mood_group
                    custom_moods_found[mood] = mood_group
            except KeyError:
                pass

        # TODO: disallow duplicates in different mood groups - what colour to use if a mood is in more than one group?
        return custom_moods_found

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self.__known_moods)

    def __eq__(self, other) -> bool:
        if isinstance(other, Moodverse):
            return self.__known_moods == other.get_moods

    def __getitem__(self, item: str) -> MoodGroup:
        """
        :param item: mood name to look up
        :return: the :class:`MoodGroup` the mood belongs to (carries ``.name`` and ``.colour``).
        :raises MoodNotFoundError: if the mood is not in the known set.
        """
        try:
            return self.__known_moods[item]
        except KeyError:
            raise MoodNotFoundError(item)

    @property
    def get_custom_moods(self) -> dict[str, MoodGroup]:
        """
        Get the dictionary of only the custom moods known to this instance of :class:`Moodverse`.
        :return: ``dict[str, MoodGroup]`` where keys are moods and values are the :class:`MoodGroup` they belong to.
        """
        return self.__custom_moods

    @property
    def get_moods(self) -> dict[str, MoodGroup]:
        """
        Get the dictionary of all moods known to this instance of :class:`Moodverse`.
        :return: ``dict[str, MoodGroup]`` where keys are moods and values are the :class:`MoodGroup` they belong to.
        """
        return self.__known_moods
