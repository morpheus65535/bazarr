"""
This gives other modules access to the gritty details about characters and the
encodings that use them.
"""

from __future__ import annotations

import html
import itertools
import re
import unicodedata
from typing import Dict

# These are the encodings we will try to fix in ftfy, in the
# order that they should be tried.
CHARMAP_ENCODINGS = [
    "latin-1",
    "sloppy-windows-1252",
    "sloppy-windows-1251",
    "sloppy-windows-1250",
    "sloppy-windows-1253",
    "sloppy-windows-1254",
    "iso-8859-2",
    "macroman",
    "cp437",
]

SINGLE_QUOTE_RE = re.compile("[\u02bc\u2018-\u201b]")
DOUBLE_QUOTE_RE = re.compile("[\u201c-\u201f]")


def _build_regexes() -> Dict[str, re.Pattern[str]]:
    """
    ENCODING_REGEXES contain reasonably fast ways to detect if we
    could represent a given string in a given encoding. The simplest one is
    the 'ascii' detector, which of course just determines if all characters
    are between U+0000 and U+007F.
    """
    # Define a regex that matches ASCII text.
    encoding_regexes = {"ascii": re.compile("^[\x00-\x7f]*$")}

    for encoding in CHARMAP_ENCODINGS:
        # Make a sequence of characters that bytes \x80 to \xFF decode to
        # in each encoding, as well as byte \x1A, which is used to represent
        # the replacement character � in the sloppy-* encodings.
        byte_range = bytes(list(range(0x80, 0x100)) + [0x1A])
        charlist = byte_range.decode(encoding)

        # The rest of the ASCII bytes -- bytes \x00 to \x19 and \x1B
        # to \x7F -- will decode as those ASCII characters in any encoding we
        # support, so we can just include them as ranges. This also lets us
        # not worry about escaping regex special characters, because all of
        # them are in the \x1B to \x7F range.
        regex = "^[\x00-\x19\x1b-\x7f{0}]*$".format(charlist)
        encoding_regexes[encoding] = re.compile(regex)
    return encoding_regexes


ENCODING_REGEXES = _build_regexes()


def _build_html_entities() -> Dict[str, str]:
    entities = {}
    # Create a dictionary based on the built-in HTML5 entity dictionary.
    # Add a limited set of HTML entities that we'll also decode if they've
    # been case-folded to uppercase, such as decoding &NTILDE; as "Ñ".
    for name, char in html.entities.html5.items():  # type: ignore
        if name.endswith(";"):
            entities["&" + name] = char

            # Restrict the set of characters we can attempt to decode if their
            # name has been uppercased. If we tried to handle all entity names,
            # the results would be ambiguous.
            if name == name.lower():
                name_upper = name.upper()
                entity_upper = "&" + name_upper
                if html.unescape(entity_upper) == entity_upper:
                    entities[entity_upper] = char.upper()
    return entities


HTML_ENTITY_RE = re.compile(r"&#?[0-9A-Za-z]{1,24};")
HTML_ENTITIES = _build_html_entities()


def possible_encoding(text: str, encoding: str) -> bool:
    """
    Given text and a single-byte encoding, check whether that text could have
    been decoded from that single-byte encoding.

    In other words, check whether it can be encoded in that encoding, possibly
    sloppily.
    """
    return bool(ENCODING_REGEXES[encoding].match(text))


def _build_control_char_mapping() -> Dict[int, None]:
    """
    Build a translate mapping that strips likely-unintended control characters.
    See :func:`ftfy.fixes.remove_control_chars` for a description of these
    codepoint ranges and why they should be removed.
    """
    control_chars: Dict[int, None] = {}

    for i in itertools.chain(
        range(0x00, 0x09),
        [0x0B],
        range(0x0E, 0x20),
        [0x7F],
        range(0x206A, 0x2070),
        [0xFEFF],
        range(0xFFF9, 0xFFFD),
    ):
        control_chars[i] = None

    return control_chars


CONTROL_CHARS = _build_control_char_mapping()


# Recognize UTF-8 sequences that would be valid if it weren't for a b'\xa0'
# that some Windows-1252 program converted to a plain space.
#
# The smaller values are included on a case-by-case basis, because we don't want
# to decode likely input sequences to unlikely characters. These are the ones
# that *do* form likely characters before 0xa0:
#
#   0xc2 -> U+A0 NO-BREAK SPACE
#   0xc3 -> U+E0 LATIN SMALL LETTER A WITH GRAVE
#   0xc5 -> U+160 LATIN CAPITAL LETTER S WITH CARON
#   0xce -> U+3A0 GREEK CAPITAL LETTER PI
#   0xd0 -> U+420 CYRILLIC CAPITAL LETTER ER
#   0xd9 -> U+660 ARABIC-INDIC DIGIT ZERO
#
# In three-character sequences, we exclude some lead bytes in some cases.
#
# When the lead byte is immediately followed by 0xA0, we shouldn't accept
# a space there, because it leads to some less-likely character ranges:
#
#   0xe0 -> Samaritan script
#   0xe1 -> Mongolian script (corresponds to Latin-1 'á' which is too common)
#
# We accept 0xe2 and 0xe3, which cover many scripts. Bytes 0xe4 and
# higher point mostly to CJK characters, which we generally don't want to
# decode near Latin lowercase letters.
#
# In four-character sequences, the lead byte must be F0, because that accounts
# for almost all of the usage of high-numbered codepoints (tag characters whose
# UTF-8 starts with the byte F3 are only used in some rare new emoji sequences).
#
# This is meant to be applied to encodings of text that tests true for `is_bad`.
# Any of these could represent characters that legitimately appear surrounded by
# spaces, particularly U+C5 (Å), which is a word in multiple languages!
#
# We should consider checking for b'\x85' being converted to ... in the future.
# I've seen it once, but the text still wasn't recoverable.

ALTERED_UTF8_RE = re.compile(
    b"[\xc2\xc3\xc5\xce\xd0\xd9][ ]"
    b"|[\xe2\xe3][ ][\x80-\x84\x86-\x9f\xa1-\xbf]"
    b"|[\xe0-\xe3][\x80-\x84\x86-\x9f\xa1-\xbf][ ]"
    b"|[\xf0][ ][\x80-\xbf][\x80-\xbf]"
    b"|[\xf0][\x80-\xbf][ ][\x80-\xbf]"
    b"|[\xf0][\x80-\xbf][\x80-\xbf][ ]"
)


# This expression matches UTF-8 and CESU-8 sequences where some of the
# continuation bytes have been lost. The byte 0x1a (sometimes written as ^Z) is
# used within ftfy to represent a byte that produced the replacement character
# \ufffd. We don't know which byte it was, but we can at least decode the UTF-8
# sequence as \ufffd instead of failing to re-decode it at all.
#
# In some cases, we allow the ASCII '?' in place of \ufffd, but at most once per
# sequence.
LOSSY_UTF8_RE = re.compile(
    b"[\xc2-\xdf][\x1a]"
    b"|[\xc2-\xc3][?]"
    b"|\xed[\xa0-\xaf][\x1a?]\xed[\xb0-\xbf][\x1a?\x80-\xbf]"
    b"|\xed[\xa0-\xaf][\x1a?\x80-\xbf]\xed[\xb0-\xbf][\x1a?]"
    b"|[\xe0-\xef][\x1a?][\x1a\x80-\xbf]"
    b"|[\xe0-\xef][\x1a\x80-\xbf][\x1a?]"
    b"|[\xf0-\xf4][\x1a?][\x1a\x80-\xbf][\x1a\x80-\xbf]"
    b"|[\xf0-\xf4][\x1a\x80-\xbf][\x1a?][\x1a\x80-\xbf]"
    b"|[\xf0-\xf4][\x1a\x80-\xbf][\x1a\x80-\xbf][\x1a?]"
    b"|\x1a"
)


# This regex matches C1 control characters, which occupy some of the positions
# in the Latin-1 character map that Windows assigns to other characters instead.
C1_CONTROL_RE = re.compile(r"[\x80-\x9f]")


# A translate mapping that breaks ligatures made of Latin letters. While
# ligatures may be important to the representation of other languages, in Latin
# letters they tend to represent a copy/paste error. It omits ligatures such
# as æ that are frequently used intentionally.
#
# This list additionally includes some Latin digraphs that represent two
# characters for legacy encoding reasons, not for typographical reasons.
#
# Ligatures and digraphs may also be separated by NFKC normalization, but that
# is sometimes more normalization than you want.

LIGATURES = {
    ord("Ĳ"): "IJ",  # Dutch ligatures
    ord("ĳ"): "ij",
    ord("ŉ"): "ʼn",  # Afrikaans digraph meant to avoid auto-curled quote
    ord("Ǳ"): "DZ",  # Serbian/Croatian digraphs for Cyrillic conversion
    ord("ǲ"): "Dz",
    ord("ǳ"): "dz",
    ord("Ǆ"): "DŽ",
    ord("ǅ"): "Dž",
    ord("ǆ"): "dž",
    ord("Ǉ"): "LJ",
    ord("ǈ"): "Lj",
    ord("ǉ"): "lj",
    ord("Ǌ"): "NJ",
    ord("ǋ"): "Nj",
    ord("ǌ"): "nj",
    ord("ﬀ"): "ff",  # Latin typographical ligatures
    ord("ﬁ"): "fi",
    ord("ﬂ"): "fl",
    ord("ﬃ"): "ffi",
    ord("ﬄ"): "ffl",
    ord("ﬅ"): "ſt",
    ord("ﬆ"): "st",
}


def _build_width_map() -> Dict[int, str]:
    """
    Build a translate mapping that replaces halfwidth and fullwidth forms
    with their standard-width forms.
    """
    # Though it's not listed as a fullwidth character, we'll want to convert
    # U+3000 IDEOGRAPHIC SPACE to U+20 SPACE on the same principle, so start
    # with that in the dictionary.
    width_map = {0x3000: " "}
    for i in range(0xFF01, 0xFFF0):
        char = chr(i)
        alternate = unicodedata.normalize("NFKC", char)
        if alternate != char:
            width_map[i] = alternate
    return width_map


WIDTH_MAP = _build_width_map()


# Character classes that help us pinpoint embedded mojibake. These can
# include common characters, because we'll also check them for 'badness'.
UTF8_CLUES = {
    # Letters that decode to 0xC2 - 0xDF in a Latin-1-like encoding
    "utf8_first_of_2": (
        "ÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßĂĆČĎĐĘĚĞİĹŃŇŐŘŞŢŮŰ"
        "ΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩΪΫάέήίВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    ),
    # Letters that decode to 0xE0 - 0xEF in a Latin-1-like encoding
    "utf8_first_of_3": ("àáâãäåæçèéêëìíîïăćčďęěĺŕΰαβγδεζηθικλμνξοабвгдежзийклмноп"),
    # Letters that decode to 0xF0 or 0xF3 in a Latin-1-like encoding.
    # (Other leading bytes correspond only to unassigned codepoints)
    "utf8_first_of_4": ("ðóđğπσру"),
    # Letters that decode to 0x80 - 0xBF in a Latin-1-like encoding,
    # including a space standing in for 0xA0
    "utf8_continuation": (
        "\x80-\xbf"
        "ĄąĽľŁłŒœŚśŞşŠšŤťŸŹźŻżŽžƒˆˇ˘˛˜˝΄΅"
        "ΆΈΉΊΌΎΏЁЂЃЄЅІЇЈЉЊЋЌЎЏёђѓєѕіїјљњћќўџҐґ"
        "–—―‘’‚“”„†‡•…‰‹›€№™"
        " "
    ),
    # Letters that decode to 0x80 - 0xBF in a Latin-1-like encoding,
    # and don't usually stand for themselves when adjacent to mojibake.
    # This excludes spaces, dashes, quotation marks, and ellipses.
    "utf8_continuation_strict": (
        "\x80-\xbf"
        "ĄąĽľŁłŒœŚśŞşŠšŤťŸŹźŻżŽžƒˆˇ˘˛˜˝΄΅"
        "ΆΈΉΊΌΎΏЁЂЃЄЅІЇЈЉЊЋЌЎЏёђѓєѕіїјљњћќўџҐґ"
        "†‡•‰‹›€№™"
    ),
}

# This regex uses UTF8_CLUES to find sequences of likely mojibake.
# It matches them with + so that several adjacent UTF-8-looking sequences
# get coalesced into one, allowing them to be fixed more efficiently
# and not requiring every individual subsequence to be detected as 'badness'.
#
# We accept spaces in place of "utf8_continuation", because spaces might have
# been intended to be U+A0 NO-BREAK SPACE.
#
# We do a lookbehind to make sure the previous character isn't a
# "utf8_continuation_strict" character, so that we don't fix just a few
# characters in a huge garble and make the situation worse.
#
# Unfortunately, the matches to this regular expression won't show their
# surrounding context, and including context would make the expression much
# less efficient. The 'badness' rules that require context, such as a preceding
# lowercase letter, will prevent some cases of inconsistent UTF-8 from being
# fixed when they don't see it.
UTF8_DETECTOR_RE = re.compile(
    """
    (?<! [{utf8_continuation_strict}])
    (
        [{utf8_first_of_2}] [{utf8_continuation}]
        |
        [{utf8_first_of_3}] [{utf8_continuation}]{{2}}
        |
        [{utf8_first_of_4}] [{utf8_continuation}]{{3}}
    )+
""".format(
        **UTF8_CLUES
    ),
    re.VERBOSE,
)
