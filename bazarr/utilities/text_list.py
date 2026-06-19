# coding=utf-8


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

        if body.startswith('None', index):
            values.append(None)
            index += 4
        elif index < len(body) and body[index] in ("'", '"'):
            quote = body[index]
            index += 1
            chars = []
            while index < len(body):
                char = body[index]
                if char == "\\":
                    index += 1
                    if index >= len(body):
                        raise ValueError
                    chars.append(body[index])
                    index += 1
                    continue
                if char == quote:
                    index += 1
                    break
                chars.append(char)
                index += 1
            else:
                raise ValueError
            values.append("".join(chars))
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
    except ValueError:
        return list(default)
