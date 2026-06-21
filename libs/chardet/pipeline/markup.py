"""Stage 1b: charset declaration extraction (HTML/XML/PEP 263)."""

from __future__ import annotations

import re

from chardet.pipeline import DETERMINISTIC_CONFIDENCE, DetectionResult
from chardet.registry import lookup_encoding

_SCAN_LIMIT = 4096

_XML_ENCODING_RE = re.compile(
    rb"""<\?xml[^>]+encoding\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE
)
_HTML5_CHARSET_RE = re.compile(
    rb"""<meta[^>]+charset\s*=\s*['"]?\s*([^\s'">;]+)""", re.IGNORECASE
)
_HTML4_CONTENT_TYPE_RE = re.compile(
    rb"""<meta[^>]+content\s*=\s*['"][^'"]*charset=([^\s'">;]+)""", re.IGNORECASE
)

# PEP 263: encoding declaration in the first two lines of a Python file.
# https://peps.python.org/pep-0263/
_PEP263_RE = re.compile(rb"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)", re.MULTILINE)


def _detect_pep263(data: bytes) -> DetectionResult | None:
    """Check the first two lines of *data* for a PEP 263 encoding declaration.

    PEP 263 declarations (e.g. ``# -*- coding: utf-8 -*-``) are only valid
    on line 1 or line 2 of a Python source file.

    :param data: The raw byte data to scan.
    :returns: A :class:`DetectionResult` with confidence 0.95, or ``None``.
    """
    # PEP 263 requires a '#' comment marker on line 1 or 2.
    if b"#" not in data[:200]:
        return None
    # Extract first two lines only.
    first_two_lines = b"\n".join(data.split(b"\n", 2)[:2])
    match = _PEP263_RE.search(first_two_lines)
    if match:
        try:
            raw_name = match.group(1).decode("ascii").strip()
        except (UnicodeDecodeError, ValueError):
            return None
        encoding = lookup_encoding(raw_name)
        if encoding is not None and _validate_bytes(data, encoding):
            return DetectionResult(
                encoding=encoding,
                confidence=DETERMINISTIC_CONFIDENCE,
                language=None,
                mime_type="text/x-python",
            )
    return None


def detect_markup_charset(data: bytes) -> DetectionResult | None:
    """Scan the first bytes of *data* for a charset declaration.

    Checks for:

    1. ``<?xml ... encoding="..."?>``
    2. ``<meta charset="...">``
    3. ``<meta http-equiv="Content-Type" content="...; charset=...">``
    4. PEP 263 ``# -*- coding: ... -*-`` (first two lines only)

    :param data: The raw byte data to scan.
    :returns: A :class:`DetectionResult` with confidence 0.95, or ``None``.
    """
    if not data:
        return None

    head = data[:_SCAN_LIMIT]

    for pattern in (_XML_ENCODING_RE, _HTML5_CHARSET_RE, _HTML4_CONTENT_TYPE_RE):
        match = pattern.search(head)
        if match:
            try:
                raw_name = match.group(1).decode("ascii").strip()
            except (UnicodeDecodeError, ValueError):
                continue
            encoding = lookup_encoding(raw_name)
            if encoding is not None and _validate_bytes(data, encoding):
                mime_type = "text/xml" if pattern is _XML_ENCODING_RE else "text/html"
                return DetectionResult(
                    encoding=encoding,
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                    mime_type=mime_type,
                )

    return _detect_pep263(data)


def _validate_bytes(data: bytes, encoding: str) -> bool:
    """Check that *data* can be decoded under *encoding* without errors.

    Only validates the first ``_SCAN_LIMIT`` bytes to avoid decoding a
    full 200 kB input just to verify a charset declaration found in the
    header.
    """
    try:
        data[:_SCAN_LIMIT].decode(encoding)
    except (UnicodeDecodeError, LookupError, ValueError):
        return False
    return True
