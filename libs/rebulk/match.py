#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes and functions related to matches
"""
import copy
import itertools
from collections import defaultdict, MutableSequence

try:
    from collections import OrderedDict  # pylint:disable=ungrouped-imports
except ImportError:  # pragma: no cover
    from ordereddict import OrderedDict  # pylint:disable=import-error
import six

from .loose import ensure_list, filter_index
from .utils import is_iterable
from .debug import defined_at


class MatchesDict(OrderedDict):
    """
    A custom dict with matches property.
    """

    def __init__(self):
        super(MatchesDict, self).__init__()
        self.matches = defaultdict(list)
        self.values_list = defaultdict(list)


class _BaseMatches(MutableSequence):
    """
    A custom list[Match] that automatically maintains name, tag, start and end lookup structures.
    """
    _base = list
    _base_add = _base.append
    _base_remove = _base.remove
    _base_extend = _base.extend

    def __init__(self, matches=None, input_string=None):  # pylint: disable=super-init-not-called
        self.input_string = input_string
        self._max_end = 0
        self._delegate = []
        self.__name_dict = None
        self.__tag_dict = None
        self.__start_dict = None
        self.__end_dict = None
        self.__index_dict = None
        if matches:
            self.extend(matches)

    @property
    def _name_dict(self):
        if self.__name_dict is None:
            self.__name_dict = defaultdict(_BaseMatches._base)
            for name, values in itertools.groupby([m for m in self._delegate if m.name], lambda item: item.name):
                _BaseMatches._base_extend(self.__name_dict[name], values)

        return self.__name_dict

    @property
    def _start_dict(self):
        if self.__start_dict is None:
            self.__start_dict = defaultdict(_BaseMatches._base)
            for start, values in itertools.groupby([m for m in self._delegate], lambda item: item.start):
                _BaseMatches._base_extend(self.__start_dict[start], values)

        return self.__start_dict

    @property
    def _end_dict(self):
        if self.__end_dict is None:
            self.__end_dict = defaultdict(_BaseMatches._base)
            for start, values in itertools.groupby([m for m in self._delegate], lambda item: item.end):
                _BaseMatches._base_extend(self.__end_dict[start], values)

        return self.__end_dict

    @property
    def _tag_dict(self):
        if self.__tag_dict is None:
            self.__tag_dict = defaultdict(_BaseMatches._base)
            for match in self._delegate:
                for tag in match.tags:
                    _BaseMatches._base_add(self.__tag_dict[tag], match)

        return self.__tag_dict

    @property
    def _index_dict(self):
        if self.__index_dict is None:
            self.__index_dict = defaultdict(_BaseMatches._base)
            for match in self._delegate:
                for index in range(*match.span):
                    _BaseMatches._base_add(self.__index_dict[index], match)

        return self.__index_dict

    def _add_match(self, match):
        """
        Add a match
        :param match:
        :type match: Match
        """
        if self.__name_dict is not None:
            if match.name:
                _BaseMatches._base_add(self._name_dict[match.name], (match))
        if self.__tag_dict is not None:
            for tag in match.tags:
                _BaseMatches._base_add(self._tag_dict[tag], match)
        if self.__start_dict is not None:
            _BaseMatches._base_add(self._start_dict[match.start], match)
        if self.__end_dict is not None:
            _BaseMatches._base_add(self._end_dict[match.end], match)
        if self.__index_dict is not None:
            for index in range(*match.span):
                _BaseMatches._base_add(self._index_dict[index], match)
        if match.end > self._max_end:
            self._max_end = match.end

    def _remove_match(self, match):
        """
        Remove a match
        :param match:
        :type match: Match
        """
        if self.__name_dict is not None:
            if match.name:
                _BaseMatches._base_remove(self._name_dict[match.name], match)
        if self.__tag_dict is not None:
            for tag in match.tags:
                _BaseMatches._base_remove(self._tag_dict[tag], match)
        if self.__start_dict is not None:
            _BaseMatches._base_remove(self._start_dict[match.start], match)
        if self.__end_dict is not None:
            _BaseMatches._base_remove(self._end_dict[match.end], match)
        if self.__index_dict is not None:
            for index in range(*match.span):
                _BaseMatches._base_remove(self._index_dict[index], match)
        if match.end >= self._max_end and not self._end_dict[match.end]:
            self._max_end = max(self._end_dict.keys())

    def previous(self, match, predicate=None, index=None):
        """
        Retrieves the nearest previous matches.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return:
        :rtype:
        """
        current = match.start
        while current > -1:
            previous_matches = self.ending(current)
            if previous_matches:
                return filter_index(previous_matches, predicate, index)
            current -= 1
        return filter_index(_BaseMatches._base(), predicate, index)

    def next(self, match, predicate=None, index=None):
        """
        Retrieves the nearest next matches.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return:
        :rtype:
        """
        current = match.start + 1
        while current <= self._max_end:
            next_matches = self.starting(current)
            if next_matches:
                return filter_index(next_matches, predicate, index)
            current += 1
        return filter_index(_BaseMatches._base(), predicate, index)

    def named(self, name, predicate=None, index=None):
        """
        Retrieves a set of Match objects that have the given name.
        :param name:
        :type name: str
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._name_dict[name]), predicate, index)

    def tagged(self, tag, predicate=None, index=None):
        """
        Retrieves a set of Match objects that have the given tag defined.
        :param tag:
        :type tag: str
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._tag_dict[tag]), predicate, index)

    def starting(self, start, predicate=None, index=None):
        """
        Retrieves a set of Match objects that starts at given index.
        :param start: the starting index
        :type start: int
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._start_dict[start]), predicate, index)

    def ending(self, end, predicate=None, index=None):
        """
        Retrieves a set of Match objects that ends at given index.
        :param end: the ending index
        :type end: int
        :param predicate:
        :type predicate:
        :return: set of matches
        :rtype: set[Match]
        """
        return filter_index(_BaseMatches._base(self._end_dict[end]), predicate, index)

    def range(self, start=0, end=None, predicate=None, index=None):
        """
        Retrieves a set of Match objects that are available in given range, sorted from start to end.
        :param start: the starting index
        :type start: int
        :param end: the ending index
        :type end: int
        :param predicate:
        :type predicate:
        :param index:
        :type index: int
        :return: set of matches
        :rtype: set[Match]
        """
        if end is None:
            end = self.max_end
        else:
            end = min(self.max_end, end)
        ret = _BaseMatches._base()
        for match in sorted(self):
            if match.start < end and match.end > start:
                ret.append(match)
        return filter_index(ret, predicate, index)

    def chain_before(self, position, seps, start=0, predicate=None, index=None):
        """
        Retrieves a list of chained matches, before position, matching predicate and separated by characters from seps
        only.
        :param position:
        :type position:
        :param seps:
        :type seps:
        :param start:
        :type start:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if hasattr(position, 'start'):
            position = position.start

        chain = _BaseMatches._base()
        position = min(self.max_end, position)

        for i in reversed(range(start, position)):
            index_matches = self.at_index(i)
            filtered_matches = [index_match for index_match in index_matches if not predicate or predicate(index_match)]
            if filtered_matches:
                for chain_match in filtered_matches:
                    if chain_match not in chain:
                        chain.append(chain_match)
            elif self.input_string[i] not in seps:
                break

        return filter_index(chain, predicate, index)

    def chain_after(self, position, seps, end=None, predicate=None, index=None):
        """
        Retrieves a list of chained matches, after position, matching predicate and separated by characters from seps
        only.
        :param position:
        :type position:
        :param seps:
        :type seps:
        :param end:
        :type end:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        if hasattr(position, 'end'):
            position = position.end
        chain = _BaseMatches._base()

        if end is None:
            end = self.max_end
        else:
            end = min(self.max_end, end)

        for i in range(position, end):
            index_matches = self.at_index(i)
            filtered_matches = [index_match for index_match in index_matches if not predicate or predicate(index_match)]
            if filtered_matches:
                for chain_match in filtered_matches:
                    if chain_match not in chain:
                        chain.append(chain_match)
            elif self.input_string[i] not in seps:
                break

        return filter_index(chain, predicate, index)

    @property
    def max_end(self):
        """
        Retrieves the maximum index.
        :return:
        """
        return max(len(self.input_string), self._max_end) if self.input_string else self._max_end

    def _hole_start(self, position, ignore=None):
        """
        Retrieves the start of hole index from position.
        :param position:
        :type position:
        :param ignore:
        :type ignore:
        :return:
        :rtype:
        """
        for lindex in reversed(range(0, position)):
            for starting in self.starting(lindex):
                if not ignore or not ignore(starting):
                    return lindex
        return 0

    def _hole_end(self, position, ignore=None):
        """
        Retrieves the end of hole index from position.
        :param position:
        :type position:
        :param ignore:
        :type ignore:
        :return:
        :rtype:
        """
        for rindex in range(position, self.max_end):
            for starting in self.starting(rindex):
                if not ignore or not ignore(starting):
                    return rindex
        return self.max_end

    def holes(self, start=0, end=None, formatter=None, ignore=None, seps=None, predicate=None,
              index=None):  # pylint: disable=too-many-branches,too-many-locals
        """
        Retrieves a set of Match objects that are not defined in given range.
        :param start:
        :type start:
        :param end:
        :type end:
        :param formatter:
        :type formatter:
        :param ignore:
        :type ignore:
        :param seps:
        :type seps:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        assert self.input_string if seps else True, "input_string must be defined when using seps parameter"
        if end is None:
            end = self.max_end
        else:
            end = min(self.max_end, end)
        ret = _BaseMatches._base()
        hole = False
        rindex = start

        loop_start = self._hole_start(start, ignore)

        for rindex in range(loop_start, end):
            current = []
            for at_index in self.at_index(rindex):
                if not ignore or not ignore(at_index):
                    current.append(at_index)

            if seps and hole and self.input_string and self.input_string[rindex] in seps:
                hole = False
                ret[-1].end = rindex
            else:
                if not current and not hole:
                    # Open a new hole match
                    hole = True
                    ret.append(Match(max(rindex, start), None, input_string=self.input_string, formatter=formatter))
                elif current and hole:
                    # Close current hole match
                    hole = False
                    ret[-1].end = rindex

        if ret and hole:
            # go the the next starting element ...
            ret[-1].end = min(self._hole_end(rindex, ignore), end)
        return filter_index(ret, predicate, index)

    def conflicting(self, match, predicate=None, index=None):
        """
        Retrieves a list of ``Match`` objects that conflicts with given match.
        :param match:
        :type match:
        :param predicate:
        :type predicate:
        :param index:
        :type index:
        :return:
        :rtype:
        """
        ret = _BaseMatches._base()

        for i in range(*match.span):
            for at_match in self.at_index(i):
                if at_match not in ret:
                    ret.append(at_match)

        ret.remove(match)

        return filter_index(ret, predicate, index)

    def at_match(self, match, predicate=None, index=None):
        """
        Retrieves a list of matches from given match.
        """
        return self.at_span(match.span, predicate, index)

    def at_span(self, span, predicate=None, index=None):
        """
        Retrieves a list of matches from given (start, end) tuple.
        """
        starting = self._index_dict[span[0]]
        ending = self._index_dict[span[1] - 1]

        merged = list(starting)
        for marker in ending:
            if marker not in merged:
                merged.append(marker)

        return filter_index(merged, predicate, index)

    def at_index(self, pos, predicate=None, index=None):
        """
        Retrieves a list of matches from given position
        """
        return filter_index(self._index_dict[pos], predicate, index)

    @property
    def names(self):
        """
        Retrieve all names.
        :return:
        """
        return self._name_dict.keys()

    @property
    def tags(self):
        """
        Retrieve all tags.
        :return:
        """
        return self._tag_dict.keys()

    def to_dict(self, details=False, first_value=False, enforce_list=False):
        """
        Converts matches to a dict object.
        :param details if True, values will be complete Match object, else it will be only string Match.value property
        :type details: bool
        :param first_value if True, only the first value will be kept. Else, multiple values will be set as a list in
        the dict.
        :type first_value: bool
        :param enforce_list: if True, value is wrapped in a list even when a single value is found. Else, list values
        are available under `values_list` property of the returned dict object.
        :type enforce_list: bool
        :return:
        :rtype: dict
        """
        ret = MatchesDict()
        for match in sorted(self):
            value = match if details else match.value
            ret.matches[match.name].append(match)
            if not enforce_list and value not in ret.values_list[match.name]:
                ret.values_list[match.name].append(value)
            if match.name in ret.keys():
                if not first_value:
                    if not isinstance(ret[match.name], list):
                        if ret[match.name] == value:
                            continue
                        ret[match.name] = [ret[match.name]]
                    else:
                        if value in ret[match.name]:
                            continue
                    ret[match.name].append(value)
            else:
                if enforce_list and not isinstance(value, list):
                    ret[match.name] = [value]
                else:
                    ret[match.name] = value
        return ret

    if six.PY2:  # pragma: no cover
        def clear(self):
            """
            Python 3 backport
            """
            del self[:]

    def __len__(self):
        return len(self._delegate)

    def __getitem__(self, index):
        ret = self._delegate[index]
        if isinstance(ret, list):
            return Matches(ret)
        return ret

    def __setitem__(self, index, match):
        self._delegate[index] = match
        if isinstance(index, slice):
            for match_item in match:
                self._add_match(match_item)
            return
        self._add_match(match)

    def __delitem__(self, index):
        match = self._delegate[index]
        del self._delegate[index]
        if isinstance(match, list):
            # if index is a slice, we has a match list
            for match_item in match:
                self._remove_match(match_item)
        else:
            self._remove_match(match)

    def __repr__(self):
        return self._delegate.__repr__()

    def insert(self, index, value):
        self._delegate.insert(index, value)
        self._add_match(value)


class Matches(_BaseMatches):
    """
    A custom list[Match] contains matches list.
    """

    def __init__(self, matches=None, input_string=None):
        self.markers = Markers(input_string=input_string)
        super(Matches, self).__init__(matches=matches, input_string=input_string)

    def _add_match(self, match):
        assert not match.marker, "A marker match should not be added to <Matches> object"
        super(Matches, self)._add_match(match)


class Markers(_BaseMatches):
    """
    A custom list[Match] containing markers list.
    """

    def __init__(self, matches=None, input_string=None):
        super(Markers, self).__init__(matches=None, input_string=input_string)

    def _add_match(self, match):
        assert match.marker, "A non-marker match should not be added to <Markers> object"
        super(Markers, self)._add_match(match)


class Match(object):
    """
    Object storing values related to a single match
    """

    def __init__(self, start, end, value=None, name=None, tags=None, marker=None, parent=None, private=None,
                 pattern=None, input_string=None, formatter=None, conflict_solver=None, **kwargs):
        # pylint: disable=unused-argument
        self.start = start
        self.end = end
        self.name = name
        self._value = value
        self.tags = ensure_list(tags)
        self.marker = marker
        self.parent = parent
        self.input_string = input_string
        self.formatter = formatter
        self.pattern = pattern
        self.private = private
        self.conflict_solver = conflict_solver
        self._children = None
        self._raw_start = None
        self._raw_end = None
        self.defined_at = pattern.defined_at if pattern else defined_at()

    @property
    def span(self):
        """
        2-tuple with start and end indices of the match
        """
        return self.start, self.end

    @property
    def children(self):
        """
        Children matches.
        """
        if self._children is None:
            self._children = Matches(None, self.input_string)
        return self._children

    @children.setter
    def children(self, value):
        self._children = value

    @property
    def value(self):
        """
        Get the value of the match, using formatter if defined.
        :return:
        :rtype:
        """
        if self._value:
            return self._value
        if self.formatter:
            return self.formatter(self.raw)
        return self.raw

    @value.setter
    def value(self, value):
        """
        Set the value (hardcode)
        :param value:
        :type value:
        :return:
        :rtype:
        """
        self._value = value  # pylint: disable=attribute-defined-outside-init

    @property
    def names(self):
        """
        Get all names of children
        :return:
        :rtype:
        """
        if not self.children:
            return set([self.name])
        ret = set()
        for child in self.children:
            for name in child.names:
                ret.add(name)
        return ret

    @property
    def raw_start(self):
        """
        start index of raw value
        :return:
        :rtype:
        """
        if self._raw_start is None:
            return self.start
        return self._raw_start

    @raw_start.setter
    def raw_start(self, value):
        """
        Set start index of raw value
        :return:
        :rtype:
        """
        self._raw_start = value

    @property
    def raw_end(self):
        """
        end index of raw value
        :return:
        :rtype:
        """
        if self._raw_end is None:
            return self.end
        return self._raw_end

    @raw_end.setter
    def raw_end(self, value):
        """
        Set end index of raw value
        :return:
        :rtype:
        """
        self._raw_end = value

    @property
    def raw(self):
        """
        Get the raw value of the match, without using hardcoded value nor formatter.
        :return:
        :rtype:
        """
        if self.input_string:
            return self.input_string[self.raw_start:self.raw_end]
        return None

    @property
    def initiator(self):
        """
        Retrieve the initiator parent of a match
        :param match:
        :type match:
        :return:
        :rtype:
        """
        match = self
        while match.parent:
            match = match.parent
        return match

    def crop(self, crops, predicate=None, index=None):
        """
        crop the match with given Match objects or spans tuples
        :param crops:
        :type crops: list or object
        :return: a list of Match objects
        :rtype: list[Match]
        """
        if not is_iterable(crops) or len(crops) == 2 and isinstance(crops[0], int):
            crops = [crops]
        initial = copy.deepcopy(self)
        ret = [initial]
        for crop in crops:
            if hasattr(crop, 'span'):
                start, end = crop.span
            else:
                start, end = crop
            for current in list(ret):
                if start <= current.start and end >= current.end:
                    # self is included in crop, remove current ...
                    ret.remove(current)
                elif start >= current.start and end <= current.end:
                    # crop is included in self, split current ...
                    right = copy.deepcopy(current)
                    current.end = start
                    if not current:
                        ret.remove(current)
                    right.start = end
                    if right:
                        ret.append(right)
                elif end <= current.end and end > current.start:
                    current.start = end
                elif start >= current.start and start < current.end:
                    current.end = start
        return filter_index(ret, predicate, index)

    def split(self, seps, predicate=None, index=None):
        """
        Split this match in multiple matches using given separators.
        :param seps:
        :type seps: string containing separator characters
        :return: list of new Match objects
        :rtype: list
        """
        split_match = copy.deepcopy(self)
        current_match = split_match
        ret = []

        for i in range(0, len(self.raw)):
            if self.raw[i] in seps:
                if not split_match:
                    split_match = copy.deepcopy(current_match)
                    current_match.end = self.start + i

            else:
                if split_match:
                    split_match.start = self.start + i
                    current_match = split_match
                    ret.append(split_match)
                    split_match = None

        return filter_index(ret, predicate, index)

    def __len__(self):
        return self.end - self.start

    def __hash__(self):
        return hash(Match) + hash(self.start) + hash(self.end) + hash(self.value)

    def __eq__(self, other):
        if isinstance(other, Match):
            return self.span == other.span and self.value == other.value and self.name == other.name and \
                   self.parent == other.parent
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Match):
            return self.span != other.span or self.value != other.value or self.name != other.name or \
                   self.parent != other.parent
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Match):
            return self.span < other.span
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Match):
            return self.span > other.span
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Match):
            return self.span <= other.span
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Match):
            return self.span >= other.span
        return NotImplemented

    def __repr__(self):
        flags = ""
        name = ""
        tags = ""
        defined = ""
        initiator = ""
        if self.initiator.value != self.value:
            initiator = "+initiator=" + self.initiator.value
        if self.private:
            flags += '+private'
        if self.name:
            name = "+name=%s" % (self.name,)
        if self.tags:
            tags = "+tags=%s" % (self.tags,)
        if self.defined_at:
            defined += "@%s" % (self.defined_at,)
        return "<%s:%s%s%s%s%s%s>" % (self.value, self.span, flags, name, tags, initiator, defined)
