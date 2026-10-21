"""Stage 1b: charset declaration extraction (HTML/XML/PEP 263) and promotion.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import re
from collections.abc import Iterator

from chardet._utils import decodes_without_error
from chardet.enums import EncodingEra
from chardet.pipeline import DETERMINISTIC_CONFIDENCE, DetectionResult, PipelineContext
from chardet.pipeline.structural import compute_structural_score
from chardet.registry import REGISTRY, lookup_encoding

# Markup charset declarations that commonly refer to a Windows superset
# encoding rather than the strict standard encoding.  Japanese web content
# almost universally declares "Shift_JIS" but actually uses CP932 extensions;
# similarly, Korean web content declares "EUC-KR" but uses CP949/UHC.
# When the declared encoding resolves to the base (key), we check whether
# the superset (second element) is a better answer.  The first element is
# the codec that the *reported* encoding name resolves to for callers:
# shift_jis_2004 is displayed as "SHIFT_JIS", which standard codec lookup
# resolves to plain shift_jis, so that is the codec whose decode must not
# break for the un-promoted name to be safe to report.
_MARKUP_SUPERSET_PROMOTIONS: dict[str, tuple[str, str]] = {
    "shift_jis_2004": ("shift_jis", "cp932"),
    "euc_kr": ("euc_kr", "cp949"),
}

_SCAN_LIMIT = 4096

# Labels that cannot describe a document whose declaration was read as
# ASCII bytes: UTF-16 and UTF-32 text would have put null bytes between the
# letters of the tag.  The WHATWG prescan reads such a label as UTF-8, and
# ``x-user-defined`` as windows-1252, so the declared page still has a
# chance of decoding under the name it is given.
_SELF_CONTRADICTING_LABELS = frozenset(
    {"utf-16", "utf-16-be", "utf-16-le", "utf-32", "utf-32-be", "utf-32-le"}
)

# A tag scan stops at the next ``<`` as well as at ``>``.  A tag that never
# closes is not a declaration either way, but with ``[^>]`` every unclosed
# ``<meta`` ran to the end of the head before failing, and a head made of
# nothing else cost a thousand times a normal one.  The price is a literal
# ``<`` inside an attribute value, which hides that one tag.
_XML_ENCODING_RE = re.compile(
    rb"""<\?xml\s[^<>]*encoding\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE
)
_META_TAG_RE = re.compile(rb"<meta\b([^<>]*)>", re.IGNORECASE)
# DOTALL so a quoted value may span lines.
_ATTR_RE = re.compile(
    rb"""([^\s=/>]+)(?:\s*=\s*(?:(["'])(.*?)\2|([^\s>"']+)))?""",
    re.IGNORECASE | re.DOTALL,
)
_CONTENT_CHARSET_RE = re.compile(
    rb"""charset[\t\n\f\r ]*=[\t\n\f\r ]*(?:(["'])([^"']+)\1|([^\s;"']+))""",
    re.IGNORECASE,
)

# PEP 263: encoding declaration in the first two lines of a Python file.
# https://peps.python.org/pep-0263/
_PEP263_RE = re.compile(rb"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")
_PEP263_BLANK_RE = re.compile(rb"^[ \t\f]*(?:[#\r]|$)")

# Charset declarations in EBCDIC-encoded markup, matched against a cp037
# decode of the head.  Letters, digits, and the anchor characters ``<``,
# ``>``, ``?``, ``=``, and ``/`` sit at the same code points in every
# supported EBCDIC code page, so the ``<meta``/``<?xml`` tag anchor, the
# ``charset=``/``encoding=`` label, and the encoding name itself decode
# correctly through cp037 regardless of which EBCDIC variant the data
# actually uses.  The tag anchor is required so plain EBCDIC prose that
# merely mentions ``encoding=NAME`` is not treated as a declaration; the
# tag span and the declaration tokens are matched by separate regexes so
# a bogus earlier ``encoding=`` token inside the same tag cannot consume
# the anchor away from the genuine ``charset=`` that follows it.  Quote
# characters are NOT invariant (e.g. cp1026 moves ``"``), so an optional
# single junk character stands in for the opening quote.  That junk
# character is grouped with its own trailing whitespace rather than left
# between two ``\s*`` runs: ``\s*X?\s*`` lets a whitespace byte land in
# either run, so a value that never arrives (``charset=`` followed by a
# long space run) backtracks over every split and makes the match
# quadratic in the whitespace length.  ``\s*(?:X\s*)?`` matches the same
# strings with one way to place each space.
_EBCDIC_TAG_RE = re.compile(r"<(?:meta|\?xml)[^<>]*", re.IGNORECASE)
_EBCDIC_DECL_RE = re.compile(
    r"(?:charset|encoding)\s*=\s*(?:[^\sA-Za-z0-9._-]\s*)?([A-Za-z][A-Za-z0-9._-]+)",
    re.IGNORECASE,
)

# High bytes: EBCDIC text is dominated by bytes >= 0x80 (Latin lowercase
# letters all sit at 0x81+; other scripts likewise), while ASCII-compatible
# markup is dominated by bytes < 0x80.
_MARKUP_HIGH_BYTES = bytes(range(0x80, 0x100))

# Minimum fraction of high bytes in the head for an EBCDIC scan to be
# worth attempting.
_EBCDIC_SCAN_MIN_HIGH_FRACTION = 0.25


def _detect_ebcdic_declaration(data: bytes) -> DetectionResult | None:
    """Look for a charset declaration in EBCDIC-encoded markup.

    The ASCII regexes cannot see declarations in EBCDIC bytes, so when the
    head looks like EBCDIC text (dominated by high bytes), decode it through
    cp037 — the EBCDIC page whose letter and digit positions are shared by
    all variants — and scan the decoded text.  Only declarations naming a
    MAINFRAME-era encoding are honoured, and the declared encoding must
    decode the whole window.  The MIME type follows the tag the declaration
    sits in.
    """
    head = data[:_SCAN_LIMIT]
    high_count = len(head) - len(head.translate(None, _MARKUP_HIGH_BYTES))
    if high_count < len(head) * _EBCDIC_SCAN_MIN_HIGH_FRACTION:
        return None
    decoded = head.decode("cp037", errors="replace")
    # Scan every declaration token inside every anchor tag: an unrelated
    # earlier ``charset=``/``encoding=`` token (a query string in an href,
    # a bogus attribute in the same tag) must not mask a genuine EBCDIC
    # declaration after it.
    for tag in _EBCDIC_TAG_RE.finditer(decoded):
        for match in _EBCDIC_DECL_RE.finditer(tag.group(0)):
            encoding = lookup_encoding(match.group(1).strip())
            if (
                encoding is not None
                and REGISTRY[encoding].era & EncodingEra.MAINFRAME
                and _validate_bytes(data, encoding)
            ):
                is_xml = tag.group(0)[1] == "?"
                return DetectionResult(
                    encoding=encoding,
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                    mime_type="text/xml" if is_xml else "text/html",
                )
    return None


def _pep263_encoding(raw_name: str) -> str | None:
    """Resolve a coding cookie the way :func:`tokenize.detect_encoding` does.

    Python folds the ``utf-8-*`` spellings to UTF-8 and ``latin-1``,
    ``iso-8859-1``, and ``iso-latin-1`` (with or without a suffix) to
    Latin-1 before it consults the codec registry, so ``iso-latin-1`` is a
    valid cookie even though no codec answers to it, and ``utf-8-sig``
    names plain UTF-8 rather than a file that starts with a mark.
    """
    name = raw_name[:12].lower().replace("_", "-")
    if name == "utf-8" or name.startswith("utf-8-"):
        return "utf-8"
    if name in ("latin-1", "iso-8859-1", "iso-latin-1") or name.startswith(
        ("latin-1-", "iso-8859-1-", "iso-latin-1-")
    ):
        return "iso8859-1"
    return lookup_encoding(raw_name)


def _detect_pep263(data: bytes) -> DetectionResult | None:
    """Check the first two lines of *data* for a PEP 263 encoding declaration.

    PEP 263 declarations (e.g. ``# -*- coding: utf-8 -*-``) are only valid
    on line 1 or line 2 of a Python source file.  Both lines have to start
    inside the first :data:`_SCAN_LIMIT` bytes, the same bound the markup
    scan uses.

    :param data: The raw byte data to scan.
    :returns: A :class:`DetectionResult` with confidence 0.95, or ``None``.
    """
    head = data[:_SCAN_LIMIT]
    # PEP 263 requires a '#' comment marker on line 1 or 2.
    if b"#" not in head:
        return None
    # Python only examines line 2 when line 1 is a comment or blank.
    lines = head.split(b"\n", 2)
    match = _PEP263_RE.match(lines[0])
    if match is None and len(lines) > 1 and _PEP263_BLANK_RE.match(lines[0]):
        match = _PEP263_RE.match(lines[1])
    if match:
        try:
            raw_name = match.group(1).decode("ascii").strip()
        except (UnicodeDecodeError, ValueError):
            return None
        encoding = _declared_encoding(data, _pep263_encoding(raw_name))
        if encoding is not None:
            return DetectionResult(
                encoding=encoding,
                confidence=DETERMINISTIC_CONFIDENCE,
                language=None,
                mime_type="text/x-python",
            )
    return None


def _strip_comments(head: bytes) -> bytes:
    """Return *head* without its ``<!-- -->`` comments.

    A declaration inside a comment is not a declaration, and the WHATWG
    prescan skips comments for that reason.  As in the prescan, the dashes
    that open a comment may also close it (``<!-->`` is a whole comment),
    and a comment that never closes runs to the end of the head.
    """
    start = head.find(b"<!--")
    if start < 0:
        return head
    parts: list[bytes] = []
    pos = 0
    while start >= 0:
        parts.append(head[pos:start])
        end = head.find(b"-->", start + 2)
        if end < 0:
            return b"".join(parts)
        pos = end + 3
        start = head.find(b"<!--", pos)
    parts.append(head[pos:])
    return b"".join(parts)


def _markup_encoding(raw_name: str) -> str | None:
    """Resolve a charset label found in ASCII-compatible markup."""
    if raw_name.lower() == "x-user-defined":
        return "cp1252"
    encoding = lookup_encoding(raw_name)
    if encoding in _SELF_CONTRADICTING_LABELS:
        return "utf-8"
    return encoding


def _meta_attributes(body: bytes) -> dict[bytes, bytes]:
    """Return the attributes of one meta tag, lowercased by name."""
    attrs: dict[bytes, bytes] = {}
    for match in _ATTR_RE.finditer(body):
        name = match.group(1).lower()
        if name in attrs:
            continue
        value = match.group(3)
        if value is None:
            value = match.group(4)
        if value is not None:
            attrs[name] = value
    return attrs


def _iter_html_charsets(head: bytes) -> Iterator[bytes]:
    """Yield charset labels from real meta declarations, in document order.

    ``charset=`` inside some other attribute (a refresh URL, a description)
    is not a declaration. A declaration is a ``charset`` attribute, or the
    ``charset`` parameter of an ``http-equiv="content-type"`` tag.
    ``name="content-type"`` is wrong by the spec but common enough in the
    wild that it counts too.
    """
    for tag in _META_TAG_RE.finditer(head):
        attrs = _meta_attributes(tag.group(1))
        charset = attrs.get(b"charset")
        if charset is not None and charset.strip():
            yield charset
            continue
        equiv = attrs.get(b"http-equiv")
        if equiv is None:
            equiv = attrs.get(b"name")
        content = attrs.get(b"content")
        if (
            equiv is not None
            and content is not None
            and equiv.strip().lower() == b"content-type"
        ):
            found = _CONTENT_CHARSET_RE.search(content)
            if found:
                yield found.group(2) if found.group(1) else found.group(3)


def detect_markup_charset(data: bytes) -> DetectionResult | None:
    """Scan the first bytes of *data* for a charset declaration.

    Checks for:

    1. ``<?xml ... encoding="..."?>``
    2. ``<meta charset="...">``
    3. ``<meta http-equiv="Content-Type" content="...; charset=...">``
       (also with ``name`` in place of ``http-equiv``)
    4. PEP 263 ``# -*- coding: ... -*-`` (first two lines only)

    Markup inside ``<!-- -->`` comments is not scanned.  A UTF-16 or UTF-32
    label is read as UTF-8 and ``x-user-defined`` as windows-1252, as in the
    WHATWG prescan, since a declaration found in ASCII bytes cannot be
    describing UTF-16 text.

    A declaration counts only if the declared encoding decodes the whole of
    *data*, or, failing that, if its Windows superset does (see
    :func:`_declared_encoding`).  A declaration that fails is skipped and
    the next one is tried, so a stale prolog does not hide a correct meta.

    :param data: The raw byte data to scan.
    :returns: A :class:`DetectionResult` with confidence 0.95, or ``None``.
    """
    if not data:
        return None

    head = _strip_comments(data[:_SCAN_LIMIT])

    match = _XML_ENCODING_RE.search(head)
    if match:
        try:
            raw_name = match.group(1).decode("ascii").strip()
        except (UnicodeDecodeError, ValueError):
            raw_name = ""
        encoding = _declared_encoding(
            data, _markup_encoding(raw_name) if raw_name else None
        )
        if encoding is not None:
            return DetectionResult(
                encoding=encoding,
                confidence=DETERMINISTIC_CONFIDENCE,
                language=None,
                mime_type="text/xml",
            )

    for raw in _iter_html_charsets(head):
        try:
            raw_name = raw.decode("ascii").strip()
        except UnicodeDecodeError:
            continue
        encoding = _declared_encoding(data, _markup_encoding(raw_name))
        if encoding is not None:
            return DetectionResult(
                encoding=encoding,
                confidence=DETERMINISTIC_CONFIDENCE,
                language=None,
                mime_type="text/html",
            )

    ebcdic_result = _detect_ebcdic_declaration(data)
    if ebcdic_result is not None:
        return ebcdic_result

    return _detect_pep263(data)


def promote_markup_superset(
    data: bytes,
    markup_result: DetectionResult,
    allowed: frozenset[str],
) -> DetectionResult:
    """Promote a markup-declared encoding to its superset when structural evidence supports it.

    If the declared encoding has a known superset (per
    :data:`_MARKUP_SUPERSET_PROMOTIONS`), the superset validates the data,
    and the superset's structural score is materially better, return a new
    result using the superset encoding.  Otherwise return *markup_result*
    unchanged.

    The decode checks read the whole input: what a caller can actually
    ``.decode()`` is a fact about their entire input, and a declared
    Shift_JIS page typically reaches its first CP932-only byte well past
    the header.  The structural comparison reads only the first
    :data:`_SCAN_LIMIT` bytes, since multi-byte structure is uniform enough
    that the ranking has converged by then.  It runs first because it is
    cheap and settles which single decode the answer needs: a 200 kB
    window decodes in a few hundred microseconds, and every declared page
    of a promotable encoding comes through here.
    """
    if markup_result.encoding is None:
        return markup_result
    promotion = _MARKUP_SUPERSET_PROMOTIONS.get(markup_result.encoding)
    if promotion is None:
        return markup_result
    reported_codec, superset_name = promotion
    if superset_name not in allowed:
        return markup_result
    promoted = DetectionResult(
        superset_name,
        markup_result.confidence,
        markup_result.language,
        markup_result.mime_type,
    )
    head = data[:_SCAN_LIMIT]
    ctx = PipelineContext()
    base_score = compute_structural_score(head, REGISTRY[markup_result.encoding], ctx)
    superset_score = compute_structural_score(head, REGISTRY[superset_name], ctx)
    if superset_score > base_score:
        # The superset fits the structure better; take it if it decodes.
        if decodes_without_error(data, superset_name):
            return promoted
        return markup_result
    # Decode-safety: if the codec the reported name resolves to cannot
    # decode the data (e.g. a declared-Shift_JIS page using CP932 NEC/IBM
    # extensions), the superset is the only answer a caller can actually
    # use with ``.decode()`` -- promote regardless of the structural tie.
    if decodes_without_error(data, reported_codec):
        return markup_result
    if decodes_without_error(data, superset_name):
        return promoted
    return markup_result


def _validate_bytes(data: bytes, encoding: str) -> bool:
    """Check that the whole of *data* decodes under *encoding*.

    A declaration is an answer only if the caller can decode what chardet
    examined with it.  The decoder stops at the first bad sequence, so a
    declaration that lies about the header fails as fast as a head-only
    check would, and a cut multi-byte sequence at the very end is tolerated
    as everywhere else.
    """
    return decodes_without_error(data, encoding)


def _declared_encoding(data: bytes, encoding: str | None) -> str | None:
    """Return the name to report for a declaration of *encoding*, or ``None``.

    When the declared encoding cannot decode the window but its Windows
    superset can (a declared EUC-KR page whose first CP949-only hangul sits
    past the header, a declared Shift_JIS page using NEC extensions), the
    superset is the answer the caller can use, so it is reported directly.
    :func:`promote_markup_superset` would reach the same name one window
    decode later.
    """
    if encoding is None:
        return None
    if _validate_bytes(data, encoding):
        return encoding
    promotion = _MARKUP_SUPERSET_PROMOTIONS.get(encoding)
    if promotion is not None and _validate_bytes(data, promotion[1]):
        return promotion[1]
    return None
