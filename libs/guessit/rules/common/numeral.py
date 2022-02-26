#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
parse numeral from various formats
"""
from rebulk.remodule import re

digital_numeral = r'\d{1,4}'

roman_numeral = r'(?=[MCDLXVI]+)M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'

english_word_numeral_list = [
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty'
]

french_word_numeral_list = [
    'zéro', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
    'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf', 'vingt'
]

french_alt_word_numeral_list = [
    'zero', 'une', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
    'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dixsept', 'dixhuit', 'dixneuf', 'vingt'
]


def __build_word_numeral(*args):
    """
    Build word numeral regexp from list.

    :param args:
    :type args:
    :param kwargs:
    :type kwargs:
    :return:
    :rtype:
    """
    re_ = None
    for word_list in args:
        for word in word_list:
            if not re_:
                re_ = r'(?:(?=\w+)'
            else:
                re_ += '|'
            re_ += word
    re_ += ')'
    return re_


word_numeral = __build_word_numeral(english_word_numeral_list, french_word_numeral_list, french_alt_word_numeral_list)

numeral = '(?:' + digital_numeral + '|' + roman_numeral + '|' + word_numeral + ')'

__romanNumeralMap = (
    ('M', 1000),
    ('CM', 900),
    ('D', 500),
    ('CD', 400),
    ('C', 100),
    ('XC', 90),
    ('L', 50),
    ('XL', 40),
    ('X', 10),
    ('IX', 9),
    ('V', 5),
    ('IV', 4),
    ('I', 1)
)

__romanNumeralPattern = re.compile('^' + roman_numeral + '$')


def __parse_roman(value):
    """
    convert Roman numeral to integer

    :param value: Value to parse
    :type value: string
    :return:
    :rtype:
    """
    if not __romanNumeralPattern.search(value):
        raise ValueError(f'Invalid Roman numeral: {value}')

    result = 0
    index = 0
    for num, integer in __romanNumeralMap:
        while value[index:index + len(num)] == num:
            result += integer
            index += len(num)
    return result


def __parse_word(value):
    """
    Convert Word numeral to integer

    :param value: Value to parse
    :type value: string
    :return:
    :rtype:
    """
    for word_list in [english_word_numeral_list, french_word_numeral_list, french_alt_word_numeral_list]:
        try:
            return word_list.index(value.lower())
        except ValueError:
            pass
    raise ValueError  # pragma: no cover


_clean_re = re.compile(r'[^\d]*(\d+)[^\d]*')


def parse_numeral(value, int_enabled=True, roman_enabled=True, word_enabled=True, clean=True):
    """
    Parse a numeric value into integer.

    :param value: Value to parse. Can be an integer, roman numeral or word.
    :type value: string
    :param int_enabled:
    :type int_enabled:
    :param roman_enabled:
    :type roman_enabled:
    :param word_enabled:
    :type word_enabled:
    :param clean:
    :type clean:
    :return: Numeric value, or None if value can't be parsed
    :rtype: int
    """
    # pylint: disable=too-many-branches
    if int_enabled:
        try:
            if clean:
                match = _clean_re.match(value)
                if match:
                    clean_value = match.group(1)
                    return int(clean_value)
            return int(value)
        except ValueError:
            pass
    if roman_enabled:
        try:
            if clean:
                for word in value.split():
                    try:
                        return __parse_roman(word.upper())
                    except ValueError:
                        pass
            return __parse_roman(value)
        except ValueError:
            pass
    if word_enabled:
        try:
            if clean:
                for word in value.split():
                    try:
                        return __parse_word(word)
                    except ValueError:  # pragma: no cover
                        pass
            return __parse_word(value)  # pragma: no cover
        except ValueError:  # pragma: no cover
            pass
    raise ValueError('Invalid numeral: ' + value)   # pragma: no cover
