"""Stage 2a: Byte sequence validity filtering.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet._utils import decodes_without_error
from chardet.registry import EncodingInfo


def filter_by_validity(
    data: bytes, candidates: tuple[EncodingInfo, ...]
) -> tuple[EncodingInfo, ...]:
    """Filter candidates to only those where *data* decodes without errors.

    :param data: The raw byte data to test.
    :param candidates: Encoding candidates to validate.
    :returns: The subset of *candidates* that can decode *data*.
    """
    if not data:
        return candidates

    return tuple(enc for enc in candidates if decodes_without_error(data, enc.name))
