# -*- coding: utf-8 -*-
"""
Heuristics to determine whether re-encoding text is actually making it
more reasonable.
"""

from __future__ import unicode_literals
import re
import unicodedata
from ftfy.chardata import chars_to_classes

# The following regex uses the mapping of character classes to ASCII
# characters defined in chardata.py and build_data.py:
#
# L = Latin capital letter
# l = Latin lowercase letter
# A = Non-latin capital or title-case letter
# a = Non-latin lowercase letter
# C = Non-cased letter (Lo)
# X = Control character (Cc)
# m = Letter modifier (Lm)
# M = Mark (Mc, Me, Mn)
# N = Miscellaneous numbers (No)
# 1 = Math symbol (Sm) or currency symbol (Sc)
# 2 = Symbol modifier (Sk)
# 3 = Other symbol (So)
# S = UTF-16 surrogate
# _ = Unassigned character
#   = Whitespace
# o = Other


def _make_weirdness_regex():
    """
    Creates a list of regexes that match 'weird' character sequences.
    The more matches there are, the weirder the text is.
    """
    groups = []

    # Match lowercase letters that are followed by non-ASCII uppercase letters
    groups.append('lA')

    # Match diacritical marks, except when they modify a non-cased letter or
    # another mark.
    #
    # You wouldn't put a diacritical mark on a digit or a space, for example.
    # You might put it on a Latin letter, but in that case there will almost
    # always be a pre-composed version, and we normalize to pre-composed
    # versions first. The cases that can't be pre-composed tend to be in
    # large scripts without case, which are in class C.
    groups.append('[^CM]M')

    # Match non-Latin characters adjacent to Latin characters.
    #
    # This is a simplification from ftfy version 2, which compared all
    # adjacent scripts. However, the ambiguities we need to resolve come from
    # encodings designed to represent Latin characters.
    groups.append('[Ll][AaC]')
    groups.append('[AaC][Ll]')

    # Match IPA letters next to capital letters.
    #
    # IPA uses lowercase letters only. Some accented capital letters next to
    # punctuation can accidentally decode as IPA letters, and an IPA letter
    # appearing next to a capital letter is a good sign that this happened.
    groups.append('[LA]i')
    groups.append('i[LA]')

    # Match non-combining diacritics. We've already set aside the common ones
    # like ^ (the CIRCUMFLEX ACCENT, repurposed as a caret, exponent sign,
    # or happy eye) and assigned them to category 'o'. The remaining ones,
    # like the diaeresis (¨), are pretty weird to see on their own instead
    # of combined with a letter.
    groups.append('2')

    # Match C1 control characters, which are almost always the result of
    # decoding Latin-1 that was meant to be Windows-1252.
    groups.append('X')

    # Match private use and unassigned characters.
    groups.append('P')
    groups.append('_')

    # Match adjacent characters from any different pair of these categories:
    # - Modifier marks (M)
    # - Letter modifiers (m)
    # - Miscellaneous numbers (N)
    # - Symbols (1 or 3, because 2 is already weird on its own)

    exclusive_categories = 'MmN13'
    for cat1 in exclusive_categories:
        others_range = ''.join(c for c in exclusive_categories if c != cat1)
        groups.append('{cat1}[{others_range}]'.format(
            cat1=cat1, others_range=others_range
        ))
    regex = '|'.join('({0})'.format(group) for group in groups)
    return re.compile(regex)

WEIRDNESS_RE = _make_weirdness_regex()

# These characters appear in mojibake but also appear commonly on their own.
# We have a slight preference to leave them alone.
COMMON_SYMBOL_RE = re.compile(
    '['
    '\N{HORIZONTAL ELLIPSIS}\N{EM DASH}\N{EN DASH}'
    '\N{LEFT SINGLE QUOTATION MARK}\N{LEFT DOUBLE QUOTATION MARK}'
    '\N{RIGHT SINGLE QUOTATION MARK}\N{RIGHT DOUBLE QUOTATION MARK}'
    '\N{INVERTED EXCLAMATION MARK}\N{INVERTED QUESTION MARK}\N{DEGREE SIGN}'
    '\N{TRADE MARK SIGN}'
    '\N{REGISTERED SIGN}'
    '\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}'
    '\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}'
    '\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}'
    '\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}'
    '\N{NO-BREAK SPACE}'
    '\N{ACUTE ACCENT}\N{MULTIPLICATION SIGN}\N{LATIN SMALL LETTER SHARP S}'
    '\ufeff'  # The byte-order mark, whose encoding 'ï»¿' looks common
    ']'
)

def sequence_weirdness(text):
    """
    Determine how often a text has unexpected characters or sequences of
    characters. This metric is used to disambiguate when text should be
    re-decoded or left as is.

    We start by normalizing text in NFC form, so that penalties for
    diacritical marks don't apply to characters that know what to do with
    them.

    The following things are deemed weird:

    - Lowercase letters followed by non-ASCII uppercase letters
    - Non-Latin characters next to Latin characters
    - Un-combined diacritical marks, unless they're stacking on non-alphabetic
      characters (in languages that do that kind of thing a lot) or other
      marks
    - C1 control characters
    - Adjacent symbols from any different pair of these categories:

        - Modifier marks
        - Letter modifiers
        - Non-digit numbers
        - Symbols (including math and currency)

    The return value is the number of instances of weirdness.
    """
    text2 = unicodedata.normalize('NFC', text)
    weirdness = len(WEIRDNESS_RE.findall(chars_to_classes(text2)))
    punct_discount = len(COMMON_SYMBOL_RE.findall(text2))
    return weirdness * 2 - punct_discount


def text_cost(text):
    """
    An overall cost function for text. Weirder is worse, but all else being
    equal, shorter strings are better.

    The overall cost is measured as the "weirdness" (see
    :func:`sequence_weirdness`) plus the length.
    """
    return sequence_weirdness(text) + len(text)
