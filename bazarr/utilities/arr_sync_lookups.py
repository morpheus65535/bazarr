# coding=utf-8

from collections.abc import Iterable, Sequence

import msgspec

from utilities.arr_types import ArrTag
from utilities.json_types import JsonValue


class ArrSyncLookups:
    """Index the tag and profile lists fetched for one sync."""

    def __init__(self, tags: Iterable[ArrTag], language_profiles: Iterable[tuple[int, str, str | None]],
                 audio_profiles: Iterable[Sequence[JsonValue]] | None) -> None:
        self._tags: dict[int, list[tuple[int, str]]] = {}
        for position, tag in enumerate(tags):
            self._tags.setdefault(tag['id'], []).append((position, tag['label']))
        self._profiles: dict[str, tuple[int, int]] = {}
        for position, (profile_id, name, tag) in enumerate(language_profiles):
            if tag is not None:
                self._profiles.setdefault(tag, (position, profile_id))
        self._audio: dict[int | float | str, list[str]] | None = None
        if audio_profiles is not None:
            self._audio = {}
            for profile in audio_profiles:
                identifier, language = profile[0], profile[1]
                if isinstance(identifier, (int, float, str)) and isinstance(language, str):
                    self._audio.setdefault(identifier, []).append(language)

    def tags(self, identifiers: Iterable[int]) -> list[str]:
        matches = (entry for identifier in set(identifiers) for entry in self._tags.get(identifier, ()))
        return [label for position, label in sorted(matches)]

    def matching_profile(self, tags: Iterable[str]) -> int | None:
        match = min((self._profiles[tag] for tag in tags if tag in self._profiles), default=None)
        return match[1] if match is not None else None

    def audio_languages(self, identifier: int | msgspec.UnsetType) -> list[str]:
        if self._audio is None:
            raise TypeError('Audio profiles are unavailable')
        if identifier is msgspec.UNSET:
            return []
        return self._audio.get(identifier, []).copy()
