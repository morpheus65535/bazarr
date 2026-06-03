# coding=utf-8

import logging
import unicodedata


logger = logging.getLogger(__name__)

_STRING_ESCAPES = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}


def _decode_repr_string(value):
    decoded = []
    index = 0
    while index < len(value):
        char = value[index]
        index += 1
        if char != "\\":
            decoded.append(char)
            continue
        if index == len(value):
            raise ValueError

        escaped = value[index]
        index += 1
        if escaped in _STRING_ESCAPES:
            decoded.append(_STRING_ESCAPES[escaped])
        elif escaped == "\n":
            continue
        elif escaped in "01234567":
            digits = [escaped]
            while index < len(value) and len(digits) < 3 and value[index] in "01234567":
                digits.append(value[index])
                index += 1
            decoded.append(chr(int("".join(digits), 8)))
        elif escaped in ("x", "u", "U"):
            width = {"x": 2, "u": 4, "U": 8}[escaped]
            digits = value[index:index + width]
            if len(digits) != width or any(char not in "0123456789abcdefABCDEF" for char in digits):
                raise ValueError
            decoded.append(chr(int(digits, 16)))
            index += width
        elif escaped == "N" and index < len(value) and value[index] == "{":
            end = value.find("}", index + 1)
            if end == -1:
                raise ValueError
            try:
                decoded.append(unicodedata.lookup(value[index + 1:end]))
            except KeyError as error:
                raise ValueError from error
            index = end + 1
        else:
            decoded.extend(("\\", escaped))

    return "".join(decoded)


def _parse_repr_list(value):
    value = value.strip()
    if value == '[]':
        return []
    if not value.startswith('[') or not value.endswith(']'):
        raise ValueError

    values = []
    body = value[1:-1].strip()
    if not body:
        return values

    index = 0
    while index < len(body):
        while index < len(body) and body[index].isspace():
            index += 1

        if body.startswith('None', index) and (
            index + 4 == len(body) or body[index + 4] == ',' or body[index + 4].isspace()
        ):
            values.append(None)
            index += 4
        elif index < len(body) and body[index] in ("'", '"'):
            quote = body[index]
            index += 1
            chars = []
            while index < len(body):
                char = body[index]
                if char == "\\":
                    if index + 1 >= len(body):
                        raise ValueError
                    chars.extend((char, body[index + 1]))
                    index += 2
                    continue
                if char == quote:
                    index += 1
                    break
                chars.append(char)
                index += 1
            else:
                raise ValueError
            values.append(_decode_repr_string("".join(chars)))
        else:
            raise ValueError

        while index < len(body) and body[index].isspace():
            index += 1
        if index == len(body):
            break
        if body[index] != ',':
            raise ValueError
        index += 1
        if index == len(body):
            raise ValueError

    return values


def parse_text_list(value):
    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if not isinstance(value, str):
        raise ValueError

    parsed = _parse_repr_list(value)

    if not isinstance(parsed, list):
        raise ValueError

    return parsed


def parse_text_list_or_default(value, default=None):
    if default is None:
        default = []

    try:
        return parse_text_list(value)
    except ValueError as error:
        logger.debug(
            "Could not parse text list %r (%s); using default",
            value,
            str(error) or "invalid text-list syntax",
        )
        return list(default)
