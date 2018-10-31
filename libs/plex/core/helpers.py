from plex.lib import six

import re
import unicodedata

def flatten(text):
    if text is None:
        return None

    # Normalize `text` to ascii
    text = normalize(text)

    # Remove special characters
    text = re.sub('[^A-Za-z0-9\s]+', '', text)

    # Merge duplicate spaces
    text = ' '.join(text.split())

    # Convert to lower-case
    return text.lower()

def normalize(text):
    if text is None:
        return None

    # Normalize unicode characters
    if type(text) is six.text_type:
        text = unicodedata.normalize('NFKD', text)

    # Ensure text is ASCII, ignore unknown characters
    text = text.encode('ascii', 'ignore')

    # Return decoded `text`
    return text.decode('ascii')

def to_iterable(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        return value

    return [value]


def synchronized(func):
    def wrapper(self, *__args, **__kw):
        self._lock.acquire()

        try:
            return func(self, *__args, **__kw)
        finally:
            self._lock.release()

    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__

    return wrapper
