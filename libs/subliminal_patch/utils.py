# coding=utf-8

import re


def sanitize(string, ignore_characters=None, default_characters={'-', ':', '(', ')', '.'}):
    """Sanitize a string to strip special characters.

    :param str string: the string to sanitize.
    :param set ignore_characters: characters to ignore.
    :return: the sanitized string.
    :rtype: str

    """
    # only deal with strings
    if string is None:
        return

    ignore_characters = ignore_characters or set()

    # replace some characters with one space
    characters = default_characters - ignore_characters
    if characters:
        string = re.sub(r'[%s]' % re.escape(''.join(characters)), ' ', string)

    # remove some characters
    characters = {'\''} - ignore_characters
    if characters:
        string = re.sub(r'[%s]' % re.escape(''.join(characters)), '', string)

    # replace multiple spaces with one
    string = re.sub(r'\s+', ' ', string)

    # strip and lower case
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
