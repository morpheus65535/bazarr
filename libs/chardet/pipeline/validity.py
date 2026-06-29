"""Stage 2a: Byte sequence validity filtering.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

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

    valid = []
    for enc in candidates:
        try:
            data.decode(enc.name, errors="strict")
            valid.append(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return tuple(valid)
