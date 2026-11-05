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
    """
    Decode the body of a Python string literal by interpreting its backslash
    escape sequences.

    The input is expected to be the content of a string literal without the
    surrounding quotes, as it would appear in the output of ``repr``. The
    function walks through the text character by character and translates
    recognised escape sequences into the characters they represent. Supported
    sequences include the standard single-character escapes (such as ``\\n``,
    ``\\t``, ``\\\\`` and quote escapes), a backslash followed by a newline
    (which is treated as a line continuation and dropped), octal escapes of
    up to three digits, hexadecimal escapes (``\\x`` with two digits,
    ``\\u`` with four digits and ``\\U`` with eight digits) and named
    Unicode escapes of the form ``\\N{NAME}``. Any backslash followed by a
    character that does not form a recognised escape sequence is preserved
    verbatim, mirroring the behaviour of Python's own literal parsing.

    :param value: Content of a string literal, without enclosing quotes,
        whose escape sequences should be decoded.
    :type value: str
    :return: The decoded string with all escape sequences replaced by the
        characters they denote.
    :rtype: str
    :raises ValueError: If the text ends with a lone backslash, if a
        hexadecimal escape does not contain the required number of valid
        hexadecimal digits, if a named Unicode escape is missing its closing
        brace, or if the name in a named Unicode escape is not a known
        Unicode character name.
    """
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
    """
    Parse a string containing the ``repr`` of a Python list whose elements are
    either ``None`` or string literals, and reconstruct the original list.

    The input is expected to look like the output of ``repr`` applied to a list
    of optional strings, e.g. a bracketed, comma-separated sequence of ``None``
    tokens and single- or double-quoted string literals. Surrounding whitespace
    is ignored and an empty list literal yields an empty list. Quoted elements
    are scanned character by character, honouring backslash escape sequences so
    that escaped quote characters do not terminate the literal prematurely; the
    raw escaped content is then decoded into its actual string value. Any
    deviation from this grammar, such as missing brackets, unterminated string
    literals, dangling backslashes, unsupported element kinds, missing commas
    between elements, or a trailing comma, is treated as a parse failure.

    :param value: Text representation of a list, as produced by ``repr``,
        containing only ``None`` values and quoted string literals.
    :type value: str
    :return: The reconstructed list, where each element is either ``None`` or
        the decoded string value of the corresponding literal.
    :rtype: list[str | None]
    :raises ValueError: If the input is not enclosed in square brackets, if an
        element is neither ``None`` nor a quoted string, if a string literal is
        unterminated or ends with an incomplete escape sequence, if elements are
        not separated by commas, or if the list ends with a trailing comma.
    """
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
    """
    Normalize a value into a list.

    If the value is already a list it is returned unchanged. A tuple is
    converted to a list. A string is interpreted as a textual list
    representation and parsed into a list. Any other type, or a string
    that does not represent a list, is rejected.

    :param value: The value to convert into a list. May be a list, a
        tuple, or a string containing a list representation.
    :type value: list or tuple or str
    :return: The resulting list.
    :rtype: list
    :raises ValueError: If the value is neither a list, a tuple, nor a
        string, or if the string does not represent a list.
    """
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
    """
    Parse a text-list string into a list, falling back to a default
    on failure.

    The given value is delegated to ``parse_text_list`` for parsing. If
    the value cannot be parsed because its syntax is invalid, the failure
    is logged at debug level together with the offending value and the
    error message, and a shallow copy of the default sequence is returned
    instead. When no default is supplied, an empty list is used as the
    fallback. The returned list is always a new object, so modifying it
    does not affect the caller's default.

    :param value: Text-list string to be parsed, typically a
        delimiter-separated sequence of textual items.
    :type value: str
    :param default: Fallback sequence of items returned when parsing of
        ``value`` fails. Defaults to an empty list if omitted or ``None``.
    :type default: list or None
    :return: List of parsed items, or a new list built from ``default``
        if the value could not be parsed.
    :rtype: list
    """
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
