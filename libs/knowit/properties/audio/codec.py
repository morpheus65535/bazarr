# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from six import text_type

from ...property import Configurable


class AudioCodec(Configurable):
    """Audio codec property."""

    @classmethod
    def _extract_key(cls, value):
        key = text_type(value).upper()
        if key.startswith('A_'):
            key = key[2:]

        # only the first part of the word. E.g.: 'AAC LC' => 'AAC'
        return key.split(' ')[0]

    @classmethod
    def _extract_fallback_key(cls, value, key):
        if '/' in key:
            return key.split('/')[0]
