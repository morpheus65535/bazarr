# -*- coding: utf-8 -*-

from __future__ import annotations

import logging
import re

from config import get_settings
from database import TableCustomScoreProfileConditions as conditions_table
from database import TableCustomScoreProfiles as profiles_table

logger = logging.getLogger(__name__)


class Condition:
    """Base class for score conditions. Every condition can take the amount
    of attributes needed from a subtitle object in order to find a match."""

    type = None
    against = ()

    # {type: provider, value: subdivx, required: False, negate: False}
    def __init__(self, value: str, required=False, negate=False, **kwargs):
        self._value = str(value)
        self._negate = negate
        self.required = required

    @classmethod
    def from_dict(cls, item: dict) -> Condition:
        """A factory method to create a condition object from a database
        dictionary."""
        try:
            new = _registered_conditions[item["type"]]
        except IndexError:
            raise NotImplementedError(f"{item} condition doesn't have a class.")

        return new(**item)

    def check(self, subtitle) -> bool:
        """Check if the condition is met against a Subtitle object. **May be implemented
        in a subclass**."""
        to_match = [str(getattr(subtitle, name, None)) for name in self.against]
        met = any(item == self._value for item in to_match)
        if met and not self._negate:
            return True

        return not met and self._negate

    def __repr__(self) -> str:
        return f"<Condition {self.type}={self._value} (r:{self.required} n:{self._negate})>"


class ProviderCondition(Condition):
    type = "provider"
    against = ("provider_name",)


class UploaderCondition(Condition):
    type = "uploader"
    against = ("uploader",)


class LanguageCondition(Condition):
    type = "language"
    against = ("language",)


class RegexCondition(Condition):
    type = "regex"
    against = ("release_info", "filename")

    def check(self, subtitle):
        to_match = [str(getattr(subtitle, name, None)) for name in self.against]
        met = re.search(rf"{self._value}", "".join(to_match)) is not None
        if met and not self._negate:
            return True

        return not met and self._negate


class CustomScoreProfile:
    table = profiles_table
    conditions_table = conditions_table

    def __init__(self, id=None, name=None, score=0, media=None):
        self.id = id
        self.name = name or "N/A"
        self.score = score
        self.media = media
        self._conditions = []
        self._conditions_loaded = False

    def load_conditions(self):
        try:
            self._conditions = [
                Condition.from_dict(item)
                for item in self.conditions_table.select()
                .where(self.conditions_table.profile_id == self.id)
                .dicts()
            ]
        except self.conditions_table.DoesNotExist:
            logger.debug("Conditions not found for %s", self)
            self._conditions = []

        self._conditions_loaded = True

    def check(self, subtitle):
        # Avoid calling the database on every score check
        if not self._conditions_loaded:
            self.load_conditions()

        # Always return False if no conditions are set
        if not self._conditions:
            logger.debug("No conditions found in db for %s", self)
            return False

        return self._check_conditions(subtitle)

    def _check_conditions(self, subtitle):
        logger.debug("Checking conditions for %s profile", self)

        matches = []
        for condition in self._conditions:
            matched = condition.check(subtitle)

            if matched is True:
                logger.debug("%s Condition met", condition)
                matches.append(True)
            elif condition.required and not matched:
                logger.debug("%s not met, discarding profile", condition)
                return False

        met = True in matches
        logger.debug("Profile conditions met? %s", met)
        return met

    def __repr__(self):
        return f"<ScoreProfile {self.name} (score: {self.score})>"


class Score:
    media = None
    defaults = {}
    profiles_table = profiles_table

    def __init__(self, load_profiles=False, **kwargs):
        self.data = self.defaults.copy()
        self.data.update(**kwargs)
        self.data["hash"] = self._hash_score()
        self._profiles = []
        self._profiles_loaded = False

        if load_profiles:
            self.load_profiles()

    def check_custom_profiles(self, subtitle, matches):
        if not self._profiles_loaded:
            self.load_profiles()

        for profile in self._profiles:
            if profile.check(subtitle):
                matches.add(profile.name)

    def load_profiles(self):
        """Load the profiles associated with the class. This method must be called
        after every custom profile creation or update."""
        try:
            self._profiles = [
                CustomScoreProfile(**item)
                for item in self.profiles_table.select()
                .where(self.profiles_table.media == self.media)
                .dicts()
            ]
            logger.debug("Loaded profiles: %s", self._profiles)
        except self.profiles_table.DoesNotExist:
            logger.debug("No score profiles found")
            self._profiles = []

        self._profiles_loaded = True

    def reset(self):
        self.data.update(self.defaults)

    def update(self, **kwargs):
        self.data.update(kwargs)

    @classmethod
    def from_config(cls, **kwargs):
        return cls(True, **kwargs)

    def get_scores(self, min_percent, special=None):
        return (
            self.max_score * (special or min_percent) / 100,
            self.max_score,
            set(list(self.scores.keys())),
        )

    @property
    def custom_profile_scores(self):
        return {item.name: item.score for item in self._profiles}

    @property
    def scores(self):
        return {**self.custom_profile_scores, **self.data}

    @property
    def max_score(self):
        return (
            self.data["hash"]
            + self.data["hearing_impaired"]
            + sum(item.score for item in self._profiles if item.score)
        )

    def _hash_score(self):
        return sum(
            val
            for key, val in self.data.items()
            if key not in ("hash", "hearing_impaired")
        )

    def __str__(self):
        return f"<{self.media} Score class>"


class SeriesScore(Score):
    media = "series"
    defaults = {
        "hash": 359,
        "series": 180,
        "year": 90,
        "season": 30,
        "episode": 30,
        "release_group": 15,
        "source": 7,
        "audio_codec": 3,
        "resolution": 2,
        "video_codec": 2,
        "hearing_impaired": 1,
        "streaming_service": 0,
        "edition": 0,
    }

    @classmethod
    def from_config(cls, **kwargs):
        return cls(True, **kwargs["series_scores"])

    def update(self, **kwargs):
        self.data.update(kwargs["series_scores"])


class MovieScore(Score):
    media = "movies"
    defaults = {
        "hash": 119,
        "title": 60,
        "year": 30,
        "release_group": 15,
        "source": 7,
        "audio_codec": 3,
        "resolution": 2,
        "video_codec": 2,
        "hearing_impaired": 1,
        "streaming_service": 0,
        "edition": 0,
    }

    @classmethod
    def from_config(cls, **kwargs):
        return cls(True, **kwargs["movie_scores"])

    def update(self, **kwargs):
        self.data.update(kwargs["movie_scores"])


_registered_conditions = {
    "provider": ProviderCondition,
    "uploader": UploaderCondition,
    "language": LanguageCondition,
    "regex": RegexCondition,
}

series_score = SeriesScore.from_config(**get_settings())
movie_score = MovieScore.from_config(**get_settings())
