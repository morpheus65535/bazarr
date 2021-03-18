# vim:fileencoding=utf-8

from io import open
import logging
import json

logger = logging.getLogger('pycountry.db')

try:
    unicode
except NameError:
    unicode = str


class Data(object):

    def __init__(self, **fields):
        self._fields = fields

    def __getattr__(self, key):
        if key not in self._fields:
            raise AttributeError
        return self._fields[key]

    def __setattr__(self, key, value):
        if key != '_fields':
            self._fields[key] = value
        super(Data, self).__setattr__(key, value)

    def __repr__(self):
        cls_name = self.__class__.__name__
        fields = ', '.join('%s=%r' % i for i in sorted(self._fields.items()))
        return '%s(%s)' % (cls_name, fields)

    def __dir__(self):
        return dir(self.__class__) + list(self._fields)


def lazy_load(f):
    def load_if_needed(self, *args, **kw):
        if not self._is_loaded:
            self._load()
        return f(self, *args, **kw)
    return load_if_needed


class Database(object):

    data_class_base = Data
    data_class_name = None
    root_key = None
    no_index = []

    def __init__(self, filename):
        self.filename = filename
        self._is_loaded = False

    def _load(self):
        self.objects = []
        self.index_names = set()
        self.indices = {}

        self.data_class = type(
            self.data_class_name, (self.data_class_base,), {})

        with open(self.filename, 'r', encoding="utf-8") as f:
            tree = json.load(f)

        for entry in tree[self.root_key]:
            obj = self.data_class(**entry)
            self.objects.append(obj)
            # Inject into index.
            for key, value in entry.items():
                if key in self.no_index:
                    continue
                index = self.indices.setdefault(key, {})
                if value in index:
                    logger.debug(
                        '%s %r already taken in index %r and will be '
                        'ignored. This is an error in the databases.' %
                        (self.data_class_name, value, key))
                index[value] = obj

        self._is_loaded = True

    # Public API

    @lazy_load
    def __iter__(self):
        return iter(self.objects)

    @lazy_load
    def __len__(self):
        return len(self.objects)

    @lazy_load
    def get(self, **kw):
        if len(kw) != 1:
            raise TypeError('Only one criteria may be given')
        field, value = kw.popitem()
        return self.indices[field][value]

    @lazy_load
    def lookup(self, value):
        # try relatively quick exact matches first
        if isinstance(value, (str, unicode)):
            value = value.lower()

        for key in self.indices:
            try:
                return self.indices[key][value]
            except LookupError:
                pass
        # then try slower case-insensitive lookups
        for candidate in self:
            for v in candidate._fields.values():
                if v is None:
                    continue
                if v.lower() == value:
                    return candidate
        raise LookupError('Could not find a record for %r' % value)
