"""
Match processors
"""
from guessit.rules.common import seps


def strip(match, chars=seps):
    """
    Strip given characters from match.

    :param chars:
    :param match:
    :return:
    """
    while match.input_string[match.start] in chars:
        match.start += 1
    while match.input_string[match.end - 1] in chars:
        match.end -= 1
    if not match:
        return False
