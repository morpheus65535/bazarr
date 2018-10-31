"""
A script to make the char_classes.dat file.

This never needs to run in normal usage. It needs to be run if the character
classes we care about change, or if a new version of Python supports a new
Unicode standard and we want it to affect our string decoding.

The file that we generate is based on Unicode 9.0, as supported by Python 3.6.
You can certainly use it in earlier versions. This simply makes sure that we
get consistent results from running ftfy on different versions of Python.

The file will be written to the current directory.
"""
from __future__ import unicode_literals
import unicodedata
import sys
import zlib
if sys.hexversion >= 0x03000000:
    unichr = chr

# L = Latin capital letter
# l = Latin lowercase letter
# A = Non-latin capital or title-case letter
# a = Non-latin lowercase letter
# C = Non-cased letter (Lo)
# X = Control character (Cc)
# m = Letter modifier (Lm)
# M = Mark (Mc, Me, Mn)
# N = Miscellaneous numbers (No)
# P = Private use (Co)
# 1 = Math symbol (Sm) or currency symbol (Sc)
# 2 = Symbol modifier (Sk)
# 3 = Other symbol (So)
# S = UTF-16 surrogate
# _ = Unassigned character
#   = Whitespace
# o = Other


def make_char_data_file(do_it_anyway=False):
    """
    Build the compressed data file 'char_classes.dat' and write it to the
    current directory.

    If you run this, run it in Python 3.6 or later. It will run in earlier
    versions, but you won't get the Unicode 9 standard, leading to inconsistent
    behavior.

    To protect against this, running this in the wrong version of Python will
    raise an error unless you pass `do_it_anyway=True`.
    """
    if sys.hexversion < 0x03060000 and not do_it_anyway:
        raise RuntimeError(
            "This function should be run in Python 3.6 or later."
        )

    cclasses = [None] * 0x110000
    for codepoint in range(0x0, 0x110000):
        char = unichr(codepoint)
        category = unicodedata.category(char)

        if (0x250 <= codepoint < 0x300) and char != 'ə':
            # IPA symbols and modifiers.
            #
            # This category excludes the schwa (ə), which is used as a normal
            # Latin letter in some languages.
            cclasses[codepoint] = 'i'
        elif category.startswith('L'):  # letters
            if unicodedata.name(char, '').startswith('LATIN'):
                if category == 'Lu':
                    cclasses[codepoint] = 'L'
                else:
                    cclasses[codepoint] = 'l'
            else:
                if category == 'Lu' or category == 'Lt':
                    cclasses[codepoint] = 'A'
                elif category == 'Ll':
                    cclasses[codepoint] = 'a'
                elif category == 'Lo':
                    cclasses[codepoint] = 'C'
                elif category == 'Lm':
                    cclasses[codepoint] = 'm'
                else:
                    raise ValueError('got some weird kind of letter')
        elif 0xfe00 <= codepoint <= 0xfe0f or 0x1f3fb <= codepoint <= 0x1f3ff:
            # Variation selectors and skin-tone modifiers have the category
            # of non-spacing marks, but they act like symbols
            cclasses[codepoint] = '3'
        elif category.startswith('M'):  # marks
            cclasses[codepoint] = 'M'
        elif category == 'No':
            cclasses[codepoint] = 'N'
        elif category == 'Sm' or category == 'Sc':
            cclasses[codepoint] = '1'
        elif category == 'Sk':
            cclasses[codepoint] = '2'
        elif category == 'So':
            cclasses[codepoint] = '3'
        elif category == 'Cc':
            cclasses[codepoint] = 'X'
        elif category == 'Cs':
            cclasses[codepoint] = 'S'
        elif category == 'Co':
            cclasses[codepoint] = 'P'
        elif category.startswith('Z'):
            cclasses[codepoint] = ' '
        elif 0x1f000 <= codepoint <= 0x1ffff:
            # This range is rapidly having emoji added to it. Assume that
            # an unassigned codepoint in this range is just a symbol we
            # don't know yet.
            cclasses[codepoint] = '3'
        elif category == 'Cn':
            cclasses[codepoint] = '_'
        else:
            cclasses[codepoint] = 'o'

    # Mark whitespace control characters as whitespace
    cclasses[9] = cclasses[10] = cclasses[12] = cclasses[13] = ' '

    # Some other exceptions for characters that are more commonly used as
    # punctuation or decoration than for their ostensible purpose.
    # For example, tilde is not usually a "math symbol", and the accents
    # `´ are much more like quotation marks than modifiers.
    for char in "^~`´˝＾｀":
        cclasses[ord(char)] = 'o'

    out = open('char_classes.dat', 'wb')
    out.write(zlib.compress(''.join(cclasses).encode('ascii')))
    out.close()

if __name__ == '__main__':
    make_char_data_file()
