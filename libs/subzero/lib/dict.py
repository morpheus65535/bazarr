# coding=utf-8


class DictProxy(object):
    store = None

    def __init__(self, d):
        self.Dict = d
        super(DictProxy, self).__init__()

        if self.store not in self.Dict or not self.Dict[self.store]:
            self.Dict[self.store] = self.setup_defaults()
        self.save()
        self.__initialized = True

    def __getattr__(self, name):
        if name in self.Dict[self.store]:
            return self.Dict[self.store][name]
        return getattr(super(DictProxy, self), name)

    def __setattr__(self, name, value):
        if not self.__dict__.has_key(
                '_DictProxy__initialized'):  # this test allows attributes to be set in the __init__ method
            return object.__setattr__(self, name, value)

        elif self.__dict__.has_key(name):  # any normal attributes are handled normally
            object.__setattr__(self, name, value)

        else:
            if name in self.Dict[self.store]:
                self.Dict[self.store][name] = value
                return
        object.__setattr__(self, name, value)

    def __cmp__(self, d):
        return cmp(self.Dict[self.store], d)

    def __contains__(self, item):
        return item in self.Dict[self.store]

    def __setitem__(self, key, item):
        self.Dict[self.store][key] = item
        self.Dict.Save()

    def __iter__(self):
        return iter(self.Dict[self.store])

    def __getitem__(self, key):
        if key in self.Dict[self.store]:
            return self.Dict[self.store][key]

    def __repr__(self):
        return repr(self.Dict[self.store])

    def __str__(self):
        return str(self.Dict[self.store])

    def __len__(self):
        return len(self.Dict[self.store].keys())

    def __delitem__(self, key):
        del self.Dict[self.store][key]

    def save(self):
        self.Dict.Save()

    def clear(self):
        del self.Dict[self.store]
        return None

    def copy(self):
        return self.Dict[self.store].copy()

    def has_key(self, k):
        return k in self.Dict[self.store]

    def pop(self, k, d=None):
        return self.Dict[self.store].pop(k, d)

    def update(self, *args, **kwargs):
        return self.Dict[self.store].update(*args, **kwargs)

    def keys(self):
        return self.Dict[self.store].keys()

    def values(self):
        return self.Dict[self.store].values()

    def items(self):
        return self.Dict[self.store].items()

    def __unicode__(self):
        return unicode(repr(self.Dict[self.store]))

    def setup_defaults(self):
        raise NotImplementedError


class Dicked(object):
    """
    mirrors a dictionary; readonly
    """
    _entries = None

    def __init__(self, **entries):
        self._entries = entries or None
        for key, value in entries.iteritems():
            self.__dict__[key] = (Dicked(**value) if isinstance(value, dict) else value)

    def has(self, key):
        return self._entries is not None and key in self._entries

    def get(self, key, default=None):
        return self._entries.get(key, default) if self._entries else default

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return unicode(self.__digged__)

    def __str__(self):
        return str(self.__digged__)

    def __lt__(self, d):
        return self._entries < d

    def __le__(self, d):
        return self._entries <= d

    def __eq__(self, d):
        if d is None and not self._entries:
            return True

        return self._entries == d

    def __ne__(self, d):
        return self._entries != d

    def __gt__(self, d):
        return self._entries > d

    def __ge__(self, d):
        return self._entries >= d

    def __getattr__(self, name):
        # fixme: this might be wildly stupid; maybe implement stuff like .iteritems() directly
        return getattr(self._entries, name, Dicked())

    @property
    def __digged__(self):
        return {key: value for key, value in self.__dict__.iteritems() if key != "_entries"}

    def __len__(self):
        return len(self.__digged__)

    def __nonzero__(self):
        return bool(self.__digged__)

    def __iter__(self):
        return iter(self.__digged__)

    def __hash__(self):
        return hash(self.__digged__)

    def __getitem__(self, name):
        if name in self._entries:
            return getattr(self, name)
        raise KeyError(name)
