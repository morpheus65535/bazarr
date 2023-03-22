import re
import typing

from rebulk.match import Match

seps = frozenset(r' [](){}+*|=-_~#/\\.,;:' + '\uff08\uff09')
suppress_chars = frozenset("'")
release_name_re = re.compile(r'(?P<release>[^\.\s]+(?:\.[^\.\s]+){2,})')


def to_words(value: str,
             separators: typing.FrozenSet[str] = seps,
             ignore_chars: typing.FrozenSet[str] = suppress_chars,
             predicate: typing.Callable[[str], bool] = lambda x: True):
    input_string = value
    start = 0
    i = 0
    word = ''
    words: typing.List[Match] = []
    for c in input_string:
        i += 1
        if c in ignore_chars:
            continue

        if c not in separators:
            word += c
            continue

        if not word:
            start = i
            continue

        end = i - 1
        if not predicate(value[start:end]):
            input_string = blank(input_string, start, end)
        else:
            words.append(Match(start, i - 1, value=word))

        word = ''
        start = i

    if word:
        if not predicate(value[start:]):
            input_string = blank(input_string, start, len(input_string))
        else:
            words.append(Match(start, i, value=word))

    for w in words:
        w.input_string = input_string

    return words


def to_combinations(words: typing.List[Match], max_items: int):
    results: typing.List[typing.List[Match]] = []
    n_words = len(words)
    cur_size = min(max_items, n_words)
    start = 0
    while cur_size > 0:
        end = start + cur_size
        if end > n_words:
            start = 0
            cur_size -= 1
            continue

        results.append(words[start:end])
        start += 1

    return results


def to_sentence(combination: typing.List[Match]):
    return ' '.join([c.value for c in combination])


def to_match(combination: typing.List[Match], value: typing.Any):
    start = combination[0].start
    end = combination[-1].end
    input_string = combination[0].input_string

    return Match(start, end, value=value, input_string=input_string)


def blank(string: str, start: int, end: int):
    return string[:start] + ''.ljust(end - start, ' ') + string[end:]


def blank_match(match: Match):
    return blank(match.input_string, match.start, match.end)


def blank_release_names(value: str):
    result = value
    match = release_name_re.search(value)
    while match:
        result = blank(result, match.start('release'), match.end('release'))
        match = release_name_re.search(value, match.end('release'))

    return result
