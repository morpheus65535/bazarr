import six

if six.PY3:

    def split(value, sep, maxsplit):
        return value.split(sep, maxsplit=maxsplit)


else:

    def split(value, sep, maxsplit):
        parts = value.split(sep)
        return parts[:maxsplit] + [
            sep.join(parts[maxsplit:]),
        ]
