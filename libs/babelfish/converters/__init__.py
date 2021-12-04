# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from pkg_resources import iter_entry_points, EntryPoint
from ..exceptions import LanguageConvertError, LanguageReverseError

try:
    # Python 3.3+
    from collections.abc import Mapping, MutableMapping
except ImportError:
    from collections import Mapping, MutableMapping


# from https://github.com/kennethreitz/requests/blob/master/requests/structures.py
class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.abc.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive:

        cid = CaseInsensitiveDict()
        cid['English'] = 'eng'
        cid['ENGLISH'] == 'eng'  # True
        list(cid) == ['English']  # True

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))


class LanguageConverter(object):
    """A :class:`LanguageConverter` supports converting an alpha3 language code with an
    alpha2 country code and a script code into a custom code

    .. attribute:: codes

        Set of possible custom codes

    """
    def convert(self, alpha3, country=None, script=None):
        """Convert an alpha3 language code with an alpha2 country code and a script code
        into a custom code

        :param string alpha3: ISO-639-3 language code
        :param country: ISO-3166 country code, if any
        :type country: string or None
        :param script: ISO-15924 script code, if any
        :type script: string or None
        :return: the corresponding custom code
        :rtype: string
        :raise: :class:`~babelfish.exceptions.LanguageConvertError`

        """
        raise NotImplementedError


class LanguageReverseConverter(LanguageConverter):
    """A :class:`LanguageConverter` able to reverse a custom code into a alpha3
    ISO-639-3 language code, alpha2 ISO-3166-1 country code and ISO-15924 script code

    """
    def reverse(self, code):
        """Reverse a custom code into alpha3, country and script code

        :param string code: custom code to reverse
        :return: the corresponding alpha3 ISO-639-3 language code, alpha2 ISO-3166-1 country code and ISO-15924 script code
        :rtype: tuple
        :raise: :class:`~babelfish.exceptions.LanguageReverseError`

        """
        raise NotImplementedError


class LanguageEquivalenceConverter(LanguageReverseConverter):
    """A :class:`LanguageEquivalenceConverter` is a utility class that allows you to easily define a
    :class:`LanguageReverseConverter` by only specifying the dict from alpha3 to their corresponding symbols.

    You must specify the dict of equivalence as a class variable named SYMBOLS.

    If you also set the class variable CASE_SENSITIVE to ``True`` then the reverse conversion function will be
    case-sensitive (it is case-insensitive by default).

    Example::

        class MyCodeConverter(babelfish.LanguageEquivalenceConverter):
            CASE_SENSITIVE = True
            SYMBOLS = {'fra': 'mycode1', 'eng': 'mycode2'}

    """
    CASE_SENSITIVE = False

    def __init__(self):
        self.codes = set()
        self.to_symbol = {}
        if self.CASE_SENSITIVE:
            self.from_symbol = {}
        else:
            self.from_symbol = CaseInsensitiveDict()

        for alpha3, symbol in self.SYMBOLS.items():
            self.to_symbol[alpha3] = symbol
            self.from_symbol[symbol] = (alpha3, None, None)
            self.codes.add(symbol)

    def convert(self, alpha3, country=None, script=None):
        try:
            return self.to_symbol[alpha3]
        except KeyError:
            raise LanguageConvertError(alpha3, country, script)

    def reverse(self, code):
        try:
            return self.from_symbol[code]
        except KeyError:
            raise LanguageReverseError(code)


class CountryConverter(object):
    """A :class:`CountryConverter` supports converting an alpha2 country code
    into a custom code

    .. attribute:: codes

        Set of possible custom codes

    """
    def convert(self, alpha2):
        """Convert an alpha2 country code into a custom code

        :param string alpha2: ISO-3166-1 language code
        :return: the corresponding custom code
        :rtype: string
        :raise: :class:`~babelfish.exceptions.CountryConvertError`

        """
        raise NotImplementedError


class CountryReverseConverter(CountryConverter):
    """A :class:`CountryConverter` able to reverse a custom code into a alpha2
    ISO-3166-1 country code

    """
    def reverse(self, code):
        """Reverse a custom code into alpha2 code

        :param string code: custom code to reverse
        :return: the corresponding alpha2 ISO-3166-1 country code
        :rtype: string
        :raise: :class:`~babelfish.exceptions.CountryReverseError`

        """
        raise NotImplementedError


class ConverterManager(object):
    """Manager for babelfish converters behaving like a dict with lazy loading

    Loading is done in this order:

    * Entry point converters
    * Registered converters
    * Internal converters

    .. attribute:: entry_point

        The entry point where to look for converters

    .. attribute:: internal_converters

        Internal converters with entry point syntax

    """
    entry_point = ''
    internal_converters = []

    def __init__(self):
        #: Registered converters with entry point syntax
        self.registered_converters = []

        #: Loaded converters
        self.converters = {}

    def __getitem__(self, name):
        """Get a converter, lazy loading it if necessary"""
        if name in self.converters:
            return self.converters[name]
        for ep in iter_entry_points(self.entry_point):
            if ep.name == name:
                self.converters[ep.name] = ep.load()()
                return self.converters[ep.name]
        for ep in (EntryPoint.parse(c) for c in self.registered_converters + self.internal_converters):
            if ep.name == name:
                # `require` argument of ep.load() is deprecated in newer versions of setuptools
                if hasattr(ep, 'resolve'):
                    plugin = ep.resolve()
                elif hasattr(ep, '_load'):
                    plugin = ep._load()
                else:
                    plugin = ep.load(require=False)
                self.converters[ep.name] = plugin()
                return self.converters[ep.name]
        raise KeyError(name)

    def __setitem__(self, name, converter):
        """Load a converter"""
        self.converters[name] = converter

    def __delitem__(self, name):
        """Unload a converter"""
        del self.converters[name]

    def __iter__(self):
        """Iterator over loaded converters"""
        return iter(self.converters)

    def register(self, entry_point):
        """Register a converter

        :param string entry_point: converter to register (entry point syntax)
        :raise: ValueError if already registered

        """
        if entry_point in self.registered_converters:
            raise ValueError('Already registered')
        self.registered_converters.insert(0, entry_point)

    def unregister(self, entry_point):
        """Unregister a converter

        :param string entry_point: converter to unregister (entry point syntax)

        """
        self.registered_converters.remove(entry_point)

    def __contains__(self, name):
        return name in self.converters
