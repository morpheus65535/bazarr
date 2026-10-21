"""Stage 0: Binary content detection."""

from __future__ import annotations

from chardet._utils import DEFAULT_MAX_BYTES, count_deleted

# Threshold: if more than this fraction of bytes are binary indicators, it's binary
_BINARY_THRESHOLD = 0.01

# Translation table that maps binary-indicator control bytes (0x00-0x08,
# 0x0E-0x1F — excludes \t \n \v \f \r) to None (deleting them) and keeps
# everything else.  len(data) - len(translated) gives the count in one
# C-level pass.
_BINARY_DELETE = bytes(range(0x09)) + bytes(range(0x0E, 0x20))

# Minimum fraction of high bytes (>= 0x80) among the *non-space* bytes for
# data to plausibly be EBCDIC text.  EBCDIC encodes all lowercase letters
# above 0x80, so genuine EBCDIC text is dominated by high bytes — but the
# EBCDIC space is 0x40, and space-padded fixed-width records (the canonical
# mainframe data shape) would dilute a whole-data fraction below any useful
# threshold, so padding is excluded from the denominator.
_EBCDIC_MIN_HIGH_FRACTION = 0.25

# Minimum fraction of EBCDIC word separators (0x40 space or 0x05 HT) in
# the data.  Text separates words or fields; a binary payload framed with
# ENQ/NAK passes the control-byte check yet has no reason to contain
# EBCDIC word structure (random bytes put each separator at ~0.4%, and
# per-record framing bytes stay well under 2%).  HT counts so that
# tab-separated record exports with no spaces are still recognized.
_EBCDIC_MIN_SPACE_FRACTION = 0.02

# The EBCDIC space, horizontal-tab, and newline bytes.
_EBCDIC_SPACE = 0x40
_EBCDIC_HT = 0x05
_EBCDIC_NL = 0x15

# High-byte deletion table for the EBCDIC plausibility check.
_HIGH_BYTES_DELETE = bytes(range(0x80, 0x100))


def is_binary(data: bytes, max_bytes: int = DEFAULT_MAX_BYTES) -> bool:
    """Return ``True`` if *data* appears to be binary (not text) content.

    :param data: The raw byte data to examine.
    :param max_bytes: Maximum number of bytes to scan.
    :returns: ``True`` if the data is classified as binary.
    """
    data = data[:max_bytes]
    if not data:
        return False

    binary_count = count_deleted(data, _BINARY_DELETE)
    if binary_count / len(data) <= _BINARY_THRESHOLD:
        return False

    # Above the threshold — but EBCDIC text uses 0x05 (HT) and 0x15 (NL) as
    # whitespace, which are binary indicators in ASCII-compatible data.  If
    # the excess comes entirely from those two bytes and the data looks
    # like EBCDIC text, treat it as text.
    #
    # EBCDIC text uses 0x05 (HT) and 0x15 (NL) as tab and newline, and both
    # are in _BINARY_DELETE, so the count excluding them is arithmetic on
    # the count including them: no second scan of the data, and the HT
    # count is needed for the space fraction below anyway.
    ht_count = data.count(_EBCDIC_HT)
    hard_count = binary_count - ht_count - data.count(_EBCDIC_NL)
    if hard_count / len(data) > _BINARY_THRESHOLD:
        return True
    space_count = data.count(_EBCDIC_SPACE) + ht_count
    non_space = len(data) - space_count
    if non_space == 0:
        return False
    high_count = count_deleted(data, _HIGH_BYTES_DELETE)
    if high_count / non_space < _EBCDIC_MIN_HIGH_FRACTION:
        return True
    return space_count / len(data) < _EBCDIC_MIN_SPACE_FRACTION
