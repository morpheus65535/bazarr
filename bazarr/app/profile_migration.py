# coding=utf-8
"""
Conversion of basic languages profile items into enhanced profile groups.

Every basic item becomes its own AND group, so the enhanced evaluator decides whether an item is satisfied the same way
the basic evaluator does. Item and group ids are renumbered from 1 in list order. The cutoff is remapped to the group
that holds the first item with the basic cutoff id, which is the item get_profile_cutoff() returns.

This module only depends on the standard library, so it can be imported from an Alembic revision and from tests.
"""
from typing import Any

ANY_CUTOFF = 65535
HI_EXCLUDED = "Excluded"


def _boolean_flag(value: object) -> str:
    """Return 'True' or 'False' for a stored boolean-like value."""
    return 'True' if str(value).lower() == 'true' else 'False'


def _hi_flag(value: object) -> str:
    """Return 'True', 'False' or 'Excluded' for a stored hearing-impaired value."""
    text = str(value).lower()
    if text == 'true':
        return 'True'
    if text == HI_EXCLUDED.lower():
        return HI_EXCLUDED
    return 'False'


def _is_language_item(item: object) -> bool:
    """Return True when an item has the language code the evaluators need."""
    return isinstance(item, dict) and isinstance(item.get('language'), str) and bool(item['language'])


def _convert_item(item: dict[str, Any], new_id: int) -> dict[str, Any]:
    """Return a copy of a basic item with the new id and normalized flags, keeping any other keys."""
    converted = dict(item)
    converted.update({
        'id': new_id,
        'forced': _boolean_flag(item.get('forced', False)),
        'hi': _hi_flag(item.get('hi', False)),
        'audio_exclude': _boolean_flag(item.get('audio_exclude', False)),
        'audio_only_include': _boolean_flag(item.get('audio_only_include', False)),
    })
    return converted


def convert_basic_profile(items: list[Any], cutoff: int | None) -> tuple[dict[str, list[dict[str, Any]]], int | None]:
    """
    Convert the raw items and cutoff of a basic languages profile into enhanced form.

    Items that are not objects with a language code are dropped, as the basic evaluator already ignores them. The
    cutoff becomes the id of the group that holds the first item with the basic cutoff id. A cutoff of 65535 is kept.
    A missing cutoff, or one that matches no usable item, becomes None, which keeps the basic "never met" behavior.

    :param items: The raw item list stored for the basic profile.
    :param cutoff: The basic profile cutoff, an item id, 65535 or None.
    :return: The enhanced items object, {"groups": [...]}, and the enhanced cutoff.
    :raises ValueError: When the profile has no item with a language code, because an enhanced profile needs a group.
    """
    usable_items = [item for item in items if _is_language_item(item)]
    if not usable_items:
        raise ValueError('a basic profile needs at least one language to be converted')

    new_cutoff: int | None = None
    if cutoff == ANY_CUTOFF:
        new_cutoff = ANY_CUTOFF
    elif cutoff:
        # Same lookup as get_profile_cutoff(): the first dict with the id, even if it has no language code.
        first_match = next((item for item in items if isinstance(item, dict) and item.get('id') == cutoff), None)
        for index, item in enumerate(usable_items, start=1):
            if item is first_match:
                new_cutoff = index
                break

    groups = [
        {'id': index, 'operator': 'AND', 'items': [_convert_item(item, index)]}
        for index, item in enumerate(usable_items, start=1)
    ]
    return {'groups': groups}, new_cutoff
