# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type

from ...property import Configurable


class VideoProfile(Configurable):
    """Video Profile property."""

    @classmethod
    def _extract_key(cls, value):
        return value.upper().split('@')[0]


class VideoProfileLevel(Configurable):
    """Video Profile Level property."""

    @classmethod
    def _extract_key(cls, value):
        values = text_type(value).upper().split('@')
        if len(values) > 1:
            value = values[1]
            return value

        # There's no level, so don't warn or report it
        return False


class VideoProfileTier(Configurable):
    """Video Profile Tier property."""

    @classmethod
    def _extract_key(cls, value):
        values = value.upper().split('@')
        if len(values) > 2:
            return values[2]

        # There's no tier, so don't warn or report it
        return False
