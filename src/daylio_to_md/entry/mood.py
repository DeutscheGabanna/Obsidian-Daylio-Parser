from __future__ import annotations

import logging
from typing import List, Optional

from daylio_to_md import utils, errors


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
    Moodverse is the single source of truth regarding moods. It always knows the bare-minimum set of moods.
    Its knowledge can be expanded with custom mood sets.
    """
    def __init__(self, moods_to_process: dict[str, List[str]] = None):
        """
        If you want to expand the standard mood set with your custom one, make sure to pass a valid mood set file.
        Even one error in the dict causes Moodverse to reject it, and it will then proceed to use just the standard set.
        :param moods_to_process: Lists of moods grouped into five dictionary keys: rad, great, neutral, bad & awful
        """
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

        self.__mood_set: dict[str, MoodGroup] = {}
        self.__has_custom_moods = False

        for group_name in ["rad", "good", "neutral", "bad", "awful"]:
            # Add the new group to the dict
            self.__mood_set[group_name] = MoodGroup(group_name)
            # Ask it to create its main mood (e.g. 'rad' for 'rad'-group)
            self.__mood_set[group_name].create_mood()

        # We can stop here and be content with our "default" / "standard" mood-set if user did not pass a custom one
        # CUSTOM PART OF INIT
        # --------------------
        if moods_to_process is not None:
            try:
                self.__expand_moodset_with_customs(moods_to_process)
            except MoodNotFoundError:
                msg = ErrorMsg.print(ErrorMsg.STANDARD_MOODS_USED, ', '.join(self.__mood_set.keys()))
                self.__logger.warning(msg)
            else:
                self.__has_custom_moods = True

    def __expand_moodset_with_customs(self, moods_to_process: dict[str, List[str]]) -> None:
        """
        Expands the knowledge of this specific :class:`Moodverse` with new custom moods passed by user.
        :param moods_to_process: Lists of str moods grouped into five dictionary keys: rad, great, neutral, bad & awful
        :raises MoodNotFoundError: if at least one mood was found to be invalid, no new moods will be saved
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

        # Use keys from standard_mood_set to navigate through the passed dictionary and add their unique moods over
        # The side effect is that keys in the passed dictionary which do not appear in standard mood set are skipped

        # e.g. I'm expecting a "rad" group to be in the dict
        for expected_mood_group in self.__mood_set.keys():
            expected_mood_group: str
            try:
                # Leap of faith - there must be a "rad" group, otherwise there's no point in continuing
                mood_group_to_transfer = moods_to_process[expected_mood_group]
            except KeyError as err:
                msg = ErrorMsg.print(ErrorMsg.MOOD_GROUP_NOT_FOUND, expected_mood_group)
                self.__logger.warning(msg)
                raise MoodNotFoundError(msg) from err
            # Go through each mood in this mood group - e.g. rad - and transfer them in the form of Mood objects
            for mood in mood_group_to_transfer:
                self.__mood_set[expected_mood_group].create_mood(mood)

    def get_mood(self, value_to_check: str) -> Optional['Mood']:
        """
        Checks if the mood exists in the currently used mood set. None if it does not.
        :param value_to_check: string with the name of the mood to find
        :return: reference to the :class:`Mood` object found in the currently used mood set or None
        """
        return next((mood_group.known_moods[value_to_check] for mood_group in self.__mood_set.values() if
                     value_to_check in mood_group.known_moods), None)

    def __getitem__(self, item: str):
        return self.__mood_set[item]

    @property
    def known_mood_groups(self):
        return self.__mood_set

    @property
    def has_custom_moods(self):
        return self.__has_custom_moods


class AbstractMood:
    """
    Provides shared methods for :class:`MoodGroup` and :class:`Mood`.
    """
    def __init__(self, value):
        if not value or isinstance(value, str) is False:
            raise ValueError
        self.__name = value

    @property
    def name(self) -> str:
        return self.__name

    def __str__(self) -> str:
        return self.__name

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)  # of object object


class MoodGroup(AbstractMood):
    """
    Mood group is an abstract way of thinking about moods, based on categorising them into different groups (or levels).

    **For example**:
    Feeling 'awesome' and 'amazing' all belong to the same group.
    Therefore, if we categorise moods to different categories, we create mood groups.
    They could, for example, range from 5 (best) to 1 (worst).

    Daylio uses 'rad', 'great', 'neutral', 'bad' & 'awful'.
    """
    def __init__(self, name_of_the_mood_group: str):
        """
        Create a :class:`MoodGroup` object with the specified name.
        :param name_of_the_mood_group: Name of the mood group you want to create.
        """
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__known_moods: dict[str, Mood] = {}

        super().__init__(name_of_the_mood_group)

    def create_mood(self, name: str = None) -> 'Mood':
        """
        Create the specified mood and append its reference to the known moods in this group.
        :param name: Name of the mood. If none provided, use the mood group name as its name (e.g. rad group -> rad).
        :return: reference to the newly created :class:`Mood` object
        """
        # e.g. if no argument is passed, MoodGroup "rad" will create a Mood "rad"
        # it's just a shorthand so that you don't have to write MoodGroup("rad").create_mood("rad")
        # └── known moods of 'rad' group
        #     └── rad
        final_name = self.name if name is None else name
        try:
            ref = Mood(final_name)
        except (EmptyValue, ValueError):
            self.__logger.warning(ErrorMsg.print(ErrorMsg.SKIPPED_INVALID_MOOD, final_name))
        # all went ok
        else:
            self.__known_moods[final_name] = ref
            return ref

    # TODO: possibly could do funky stuff with multiple inheritance - this method could come from Moodverse
    @property
    def known_moods(self) -> dict[str, 'Mood']:
        return self.__known_moods

    # TODO: possibly could do funky stuff with multiple inheritance - this method could come from Moodverse
    # I cannot type hint that this method returns a Mood object because of evaluation of annotations problem
    # It is discussed here: https://peps.python.org/pep-0563/
    # I could resolve it with ``from __future__ import annotations``, however it requires more recent Python versions
    # Right now I go around the problem by providing the class name in apostrophes
    def __getitem__(self, item: str) -> 'Mood':
        """
        Access the mood in this mood group.
        :raises KeyError: there is no such mood in this mood group.
        :param item: Which mood would you like to access?
        :return: reference to the mood object
        """
        if item in self.__known_moods:
            return self.__known_moods[item]
        raise KeyError

    def __eq__(self, other: List[str]) -> bool:
        """
        Does this mood group contain exactly the same moods as in the passed list.
        If other types of objects are passed rather than List[str], call the higher-ups.
        :param other: list of moods in string format to compare the mood group to
        :return: bool
        """
        # Used to compare instance of this class to ["mood", "mood", "mood"] and check if they contain the same moods
        if isinstance(other, list) and all(isinstance(item, str) for item in other):
            # I'm not sure why, but set() instead of pure array makes sure that the order is irrelevant
            # therefore ["nice", "good"] == ["good", "nice"] is Truthy, as expected
            return set([str(obj) for obj in self.known_moods]) == set(other)
        # Call the superclass' __eq__ for any other comparison
        return super().__eq__(other)


class Mood(AbstractMood):
    """
    A specific mood that belongs to a specific mood group.

    *For example*:

    - rad is a mood. It belongs to rad group.
    - awesome is a mood. It also belongs to the rad group.
    - hungry is a mood. It belongs either to neutral, bad or awful mood groups, depending on user preferences I guess"""
    def __init__(self, value: str):
        super().__init__(value)
