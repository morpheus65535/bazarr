# coding=utf-8

from __future__ import absolute_import
import re
import unicodedata

DEFAULT_CHARACTERS = {'-', ':', '(', ')', '.', '!', '?', ',', ';', '/', '¡', '¿'}


def sanitize(string, ignore_characters=None, default_characters=None):
    """Sanitize a string to strip special characters and normalize accents.

    :param str string: the string to sanitize.
    :param set ignore_characters: characters to ignore.
    :param set default_characters: characters to replace with space.
    :return: the sanitized string.
    :rtype: str

    """
    # only deal with strings
    if not isinstance(string, str):
        return

    ignore_characters = ignore_characters or set()

    if default_characters is None:
        default_characters = DEFAULT_CHARACTERS
    else:
        default_characters = set(default_characters) | {'!', '?'}

    # 1. Normalize unicode characters (NFKD decomposes accents and normalizes full-width forms)
    decomposed = unicodedata.normalize('NFKD', string)
    result = []
    for c in decomposed:
        if unicodedata.category(c) == 'Mn':
            # Strip combining diacritical marks from Latin characters (e.g. é -> e, ñ -> n, ä -> a)
            if result and (('a' <= result[-1].lower() <= 'z') or result[-1] in 'œæ'):
                continue
        result.append(c)
    string = unicodedata.normalize('NFC', ''.join(result))

    # 2. Replace punctuation with one space
    characters = default_characters - ignore_characters
    if characters:
        string = re.sub(r'[%s]' % re.escape(''.join(characters)), ' ', string)

    # 3. Remove quotes / apostrophes
    characters = {'\'', '´', '`', '’'} - ignore_characters
    if characters:
        string = re.sub(r'[%s]' % re.escape(''.join(characters)), '', string)

    # 4. Replace multiple spaces with one
    string = re.sub(r'\s+', ' ', string)

    # 5. Strip and lower case
    return string.strip().lower()


def fix_inconsistent_naming(title, inconsistent_titles_dict=None, no_sanitize=False):
    """Fix titles with inconsistent naming using dictionary and sanitize them.

    :param str title: original title.
    :param dict inconsistent_titles_dict: dictionary of titles with inconsistent naming.
    :param bool no_sanitize: indication to not sanitize title.
    :return: new title.
    :rtype: str

    """
    # only deal with strings
    if title is None:
        return

    # fix titles with inconsistent naming using dictionary
    inconsistent_titles_dict = inconsistent_titles_dict or {}
    if inconsistent_titles_dict:
        pattern = re.compile('|'.join(re.escape(key) for key in inconsistent_titles_dict.keys()))
        title = pattern.sub(lambda x: inconsistent_titles_dict[x.group()], title)

    if no_sanitize:
        return title
    else:
        return sanitize(title)
    # return fixed and sanitized title
