from __future__ import annotations

from dynaconf.utils import upperfy


class PrefixFilter:
    def __init__(self, prefix):
        if not isinstance(prefix, str):
            raise TypeError("`SETTINGS_FILE_PREFIX` must be str")
        self.prefix = f"{upperfy(prefix)}_"

    def __call__(self, data):
        """Filter incoming data by prefix"""
        len_prefix = len(self.prefix)
        return {
            upperfy(key[len_prefix:]): value
            for key, value in data.items()
            if upperfy(key[:len_prefix]) == self.prefix
        }
