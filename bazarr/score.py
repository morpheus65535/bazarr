# -*- coding: utf-8 -*-

import logging
import re

from config import get_settings
from database import TableCustomScoreProfileConditions as conditions_table
from database import TableCustomScoreProfiles as profiles_table

logger = logging.getLogger(__name__)


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
            self._conditions = list(
                self.conditions_table.select()
                .where(self.conditions_table.profile_id == self.id)
                .dicts()
            )
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
            logger.debug("No conditions found in %s profile", self)
            return False

        logger.debug("Checking conditions for %s profile", self)
        met = self._check_conditions(subtitle)
        logger.debug("Profile conditions met? %s", met)
        return met

    def _check_conditions(self, subtitle):
        checkers = {
            "provider": subtitle.provider_name,
            "uploader": subtitle.uploader,
            "language": subtitle.language,
            "regex": subtitle.release_info,
        }

        matches = []
        for condition in self._conditions:
            # Condition dict example:
            # {type: provider, value: subdivx, required: False, negate: False}
            key = condition.get("type")
            sub_value = checkers.get(key)
            if sub_value is None:
                continue

            cond_value = condition.get("value", "")
            negate = condition.get("negate", False)

            logger.debug("Checking %s: %s (condition: %s)", key, sub_value, condition)

            if key == "regex" and re.findall(rf"{cond_value}", sub_value):
                logger.debug("Regex matched: %s -> %s", cond_value, sub_value)
                matches.append(not negate and True)

            elif cond_value == sub_value:
                logger.debug("%s condition met: %s -> %s", key, cond_value, sub_value)
                matches.append(not negate and True)

            # Return False if any required condition is not met
            elif condition.get("required"):
                logger.debug("%s required condition not met, discarding profile", key)
                return False

        return True in matches

    def __repr__(self):
        return f"<ScoreProfile {self.name} (score: {self.score})>"


class Score:
    media = None
    defaults = {}
    profiles_table = profiles_table

    def __init__(self, load_profiles=False, **kwargs):
        self.data = self.defaults.copy()
        self.data.update(**kwargs)
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
            sum(val for val in self.scores.values() if val > 0)
            + sum(item.score for item in self._profiles if item.score > 0)
            - self.data["hash"]
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


series_score = SeriesScore.from_config(**get_settings())
movie_score = MovieScore.from_config(**get_settings())
