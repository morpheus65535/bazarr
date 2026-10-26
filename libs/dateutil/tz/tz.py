# -*- coding: utf-8 -*-
"""
This module offers timezone implementations subclassing the abstract
:py:class:`datetime.tzinfo` type. There are classes to handle tzfile format
files (usually are in :file:`/etc/localtime`, :file:`/usr/share/zoneinfo`,
etc), TZ environment string (in all known formats), given ranges (with help
from relative deltas), local machine timezone, fixed offset timezone, and UTC
timezone.
"""

import bisect
import datetime
import os
import struct
import sys
import time
import warnings
import weakref
from collections import OrderedDict

import six
from six import string_types
from six.moves import _thread

from .. import _tzdata_impl
from . import _tzpath
from ._common import (
    _tzinfo,
    _validate_fromutc_inputs,
    enfold,
    tzname_in_python2,
    tzrangebase,
)
from ._factories import _TzOffsetFactory, _TzSingleton, _TzStrFactory
from ._tzfile import tzfile

try:
    from .win import tzwin, tzwinlocal
except ImportError:
    tzwin = tzwinlocal = None

# For warning about rounding tzinfo
from warnings import warn

ZERO = datetime.timedelta(0)
EPOCH = datetime.datetime(1970, 1, 1, 0, 0)


@six.add_metaclass(_TzSingleton)
class tzutc(datetime.tzinfo):
    """
    This is a tzinfo object that represents the UTC time zone.

    **Examples:**

    .. doctest::

        >>> from datetime import *
        >>> from dateutil.tz import *

        >>> datetime.now()
        datetime.datetime(2003, 9, 27, 9, 40, 1, 521290)

        >>> datetime.now(tzutc())
        datetime.datetime(2003, 9, 27, 12, 40, 12, 156379, tzinfo=tzutc())

        >>> datetime.now(tzutc()).tzname()
        'UTC'

    .. versionchanged:: 2.7.0
        ``tzutc()`` is now a singleton, so the result of ``tzutc()`` will
        always return the same object.

        .. doctest::

            >>> from dateutil.tz import tzutc, UTC
            >>> tzutc() is tzutc()
            True
            >>> tzutc() is UTC
            True
    """
    def utcoffset(self, dt):
        return ZERO

    def dst(self, dt):
        return ZERO

    @tzname_in_python2
    def tzname(self, dt):
        return "UTC"

    def is_ambiguous(self, dt):
        """
        Whether or not the "wall time" of a given datetime is ambiguous in this
        zone.

        :param dt:
            A :py:class:`datetime.datetime`, naive or time zone aware.


        :return:
            Returns ``True`` if ambiguous, ``False`` otherwise.

        .. versionadded:: 2.6.0
        """
        return False

    @_validate_fromutc_inputs
    def fromutc(self, dt):
        """
        Fast track version of fromutc() returns the original ``dt`` object for
        any valid :py:class:`datetime.datetime` object.
        """
        return dt

    def __eq__(self, other):
        if not isinstance(other, (tzutc, tzoffset)):
            return NotImplemented

        return (isinstance(other, tzutc) or
                (isinstance(other, tzoffset) and other._offset == ZERO))

    __hash__ = None

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    __reduce__ = object.__reduce__


#: Convenience constant providing a :class:`tzutc()` instance
#:
#: .. versionadded:: 2.7.0
UTC = tzutc()


@six.add_metaclass(_TzOffsetFactory)
class tzoffset(datetime.tzinfo):
    """
    A simple class for representing a fixed offset from UTC.

    :param name:
        The timezone name, to be returned when ``tzname()`` is called.
    :param offset:
        The time zone offset in seconds, or (since version 2.6.0, represented
        as a :py:class:`datetime.timedelta` object).
    """
    def __init__(self, name, offset):
        self._name = name

        try:
            # Allow a timedelta
            offset = offset.total_seconds()
        except (TypeError, AttributeError):
            pass

        self._offset = datetime.timedelta(seconds=_get_supported_offset(offset))

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return ZERO

    @tzname_in_python2
    def tzname(self, dt):
        return self._name

    @_validate_fromutc_inputs
    def fromutc(self, dt):
        return dt + self._offset

    def is_ambiguous(self, dt):
        """
        Whether or not the "wall time" of a given datetime is ambiguous in this
        zone.

        :param dt:
            A :py:class:`datetime.datetime`, naive or time zone aware.
        :return:
            Returns ``True`` if ambiguous, ``False`` otherwise.

        .. versionadded:: 2.6.0
        """
        return False

    def __eq__(self, other):
        if not isinstance(other, tzoffset):
            return NotImplemented

        return self._offset == other._offset

    __hash__ = None

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self._name),
                               int(self._offset.total_seconds()))

    __reduce__ = object.__reduce__


class tzlocal(_tzinfo):
    """
    A :class:`tzinfo` subclass built around the ``time`` timezone functions.
    """
    def __init__(self):
        super(tzlocal, self).__init__()

        self._std_offset = datetime.timedelta(seconds=-time.timezone)
        if time.daylight:
            self._dst_offset = datetime.timedelta(seconds=-time.altzone)
        else:
            self._dst_offset = self._std_offset

        self._dst_saved = self._dst_offset - self._std_offset
        self._hasdst = bool(self._dst_saved)
        self._tznames = tuple(time.tzname)

    def utcoffset(self, dt):
        if dt is None and self._hasdst:
            return None

        if self._isdst(dt):
            return self._dst_offset
        else:
            return self._std_offset

    def dst(self, dt):
        if dt is None and self._hasdst:
            return None

        if self._isdst(dt):
            return self._dst_offset - self._std_offset
        else:
            return ZERO

    @tzname_in_python2
    def tzname(self, dt):
        return self._tznames[self._isdst(dt)]

    def is_ambiguous(self, dt):
        """
        Whether or not the "wall time" of a given datetime is ambiguous in this
        zone.

        :param dt:
            A :py:class:`datetime.datetime`, naive or time zone aware.


        :return:
            Returns ``True`` if ambiguous, ``False`` otherwise.

        .. versionadded:: 2.6.0
        """
        naive_dst = self._naive_is_dst(dt)
        return (not naive_dst and
                (naive_dst != self._naive_is_dst(dt - self._dst_saved)))

    def _naive_is_dst(self, dt):
        timestamp = _datetime_to_timestamp(dt)
        return time.localtime(timestamp + time.timezone).tm_isdst

    def _isdst(self, dt, fold_naive=True):
        # We can't use mktime here. It is unstable when deciding if
        # the hour near to a change is DST or not.
        #
        # timestamp = time.mktime((dt.year, dt.month, dt.day, dt.hour,
        #                         dt.minute, dt.second, dt.weekday(), 0, -1))
        # return time.localtime(timestamp).tm_isdst
        #
        # The code above yields the following result:
        #
        # >>> import tz, datetime
        # >>> t = tz.tzlocal()
        # >>> datetime.datetime(2003,2,15,23,tzinfo=t).tzname()
        # 'BRDT'
        # >>> datetime.datetime(2003,2,16,0,tzinfo=t).tzname()
        # 'BRST'
        # >>> datetime.datetime(2003,2,15,23,tzinfo=t).tzname()
        # 'BRST'
        # >>> datetime.datetime(2003,2,15,22,tzinfo=t).tzname()
        # 'BRDT'
        # >>> datetime.datetime(2003,2,15,23,tzinfo=t).tzname()
        # 'BRDT'
        #
        # Here is a more stable implementation:
        #
        if not self._hasdst:
            return False

        # Check for ambiguous times:
        dstval = self._naive_is_dst(dt)
        fold = getattr(dt, 'fold', None)

        if self.is_ambiguous(dt):
            if fold is not None:
                return not self._fold(dt)
            else:
                return True

        return dstval

    def __eq__(self, other):
        if isinstance(other, tzlocal):
            return (self._std_offset == other._std_offset and
                    self._dst_offset == other._dst_offset)
        elif isinstance(other, tzutc):
            return (not self._hasdst and
                    self._tznames[0] in {'UTC', 'GMT'} and
                    self._std_offset == ZERO)
        elif isinstance(other, tzoffset):
            return (not self._hasdst and
                    self._tznames[0] == other._name and
                    self._std_offset == other._offset)
        else:
            return NotImplemented

    __hash__ = None

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    __reduce__ = object.__reduce__


class tzrange(tzrangebase):
    """
    The ``tzrange`` object is a time zone specified by a set of offsets and
    abbreviations, equivalent to the way the ``TZ`` variable can be specified
    in POSIX-like systems, but using Python delta objects to specify DST
    start, end and offsets.

    :param stdabbr:
        The abbreviation for standard time (e.g. ``'EST'``).

    :param stdoffset:
        An integer or :class:`datetime.timedelta` object or equivalent
        specifying the base offset from UTC.

        If unspecified, +00:00 is used.

    :param dstabbr:
        The abbreviation for DST / "Summer" time (e.g. ``'EDT'``).

        If specified, with no other DST information, DST is assumed to occur
        and the default behavior or ``dstoffset``, ``start`` and ``end`` is
        used. If unspecified and no other DST information is specified, it
        is assumed that this zone has no DST.

        If this is unspecified and other DST information is *is* specified,
        DST occurs in the zone but the time zone abbreviation is left
        unchanged.

    :param dstoffset:
        A an integer or :class:`datetime.timedelta` object or equivalent
        specifying the UTC offset during DST. If unspecified and any other DST
        information is specified, it is assumed to be the STD offset +1 hour.

    :param start:
        A :class:`relativedelta.relativedelta` object or equivalent specifying
        the time and time of year that daylight savings time starts. To
        specify, for example, that DST starts at 2AM on the 2nd Sunday in
        March, pass:

            ``relativedelta(hours=2, month=3, day=1, weekday=SU(+2))``

        If unspecified and any other DST information is specified, the default
        value is 2 AM on the first Sunday in April.

    :param end:
        A :class:`relativedelta.relativedelta` object or equivalent
        representing the time and time of year that daylight savings time
        ends, with the same specification method as in ``start``. One note is
        that this should point to the first time in the *standard* zone, so if
        a transition occurs at 2AM in the DST zone and the clocks are set back
        1 hour to 1AM, set the ``hours`` parameter to +1.


    **Examples:**

    .. testsetup:: tzrange

        from dateutil.tz import tzrange, tzstr

    .. doctest:: tzrange

        >>> tzstr('EST5EDT') == tzrange("EST", -18000, "EDT")
        True

        >>> from dateutil.relativedelta import *
        >>> range1 = tzrange("EST", -18000, "EDT")
        >>> range2 = tzrange("EST", -18000, "EDT", -14400,
        ...                  relativedelta(hours=+2, month=4, day=1,
        ...                                weekday=SU(+1)),
        ...                  relativedelta(hours=+1, month=10, day=31,
        ...                                weekday=SU(-1)))
        >>> tzstr('EST5EDT') == range1 == range2
        True

    """
    def __init__(self, stdabbr, stdoffset=None,
                 dstabbr=None, dstoffset=None,
                 start=None, end=None):

        global relativedelta
        from dateutil import relativedelta

        self._std_abbr = stdabbr
        self._dst_abbr = dstabbr

        try:
            stdoffset = stdoffset.total_seconds()
        except (TypeError, AttributeError):
            pass

        try:
            dstoffset = dstoffset.total_seconds()
        except (TypeError, AttributeError):
            pass

        if stdoffset is not None:
            self._std_offset = datetime.timedelta(seconds=stdoffset)
        else:
            self._std_offset = ZERO

        if dstoffset is not None:
            self._dst_offset = datetime.timedelta(seconds=dstoffset)
        elif dstabbr and stdoffset is not None:
            self._dst_offset = self._std_offset + datetime.timedelta(hours=+1)
        else:
            self._dst_offset = ZERO

        if dstabbr and start is None:
            self._start_delta = relativedelta.relativedelta(
                hours=+2, month=4, day=1, weekday=relativedelta.SU(+1))
        else:
            self._start_delta = start

        if dstabbr and end is None:
            self._end_delta = relativedelta.relativedelta(
                hours=+1, month=10, day=31, weekday=relativedelta.SU(-1))
        else:
            self._end_delta = end

        self._dst_base_offset_ = self._dst_offset - self._std_offset
        self.hasdst = bool(self._start_delta)

    def transitions(self, year):
        """
        For a given year, get the DST on and off transition times, expressed
        always on the standard time side. For zones with no transitions, this
        function returns ``None``.

        :param year:
            The year whose transitions you would like to query.

        :return:
            Returns a :class:`tuple` of :class:`datetime.datetime` objects,
            ``(dston, dstoff)`` for zones with an annual DST transition, or
            ``None`` for fixed offset zones.
        """
        if not self.hasdst:
            return None

        base_year = datetime.datetime(year, 1, 1)

        start = base_year + self._start_delta
        end = base_year + self._end_delta

        return (start, end)

    def __eq__(self, other):
        if not isinstance(other, tzrange):
            return NotImplemented

        return (self._std_abbr == other._std_abbr and
                self._dst_abbr == other._dst_abbr and
                self._std_offset == other._std_offset and
                self._dst_offset == other._dst_offset and
                self._start_delta == other._start_delta and
                self._end_delta == other._end_delta)

    @property
    def _dst_base_offset(self):
        return self._dst_base_offset_


@six.add_metaclass(_TzStrFactory)
class tzstr(tzrange):
    """
    ``tzstr`` objects are time zone objects specified by a time-zone string as
    it would be passed to a ``TZ`` variable on POSIX-style systems (see
    the `GNU C Library: TZ Variable`_ for more details).

    There is one notable exception, which is that POSIX-style time zones use an
    inverted offset format, so normally ``GMT+3`` would be parsed as an offset
    3 hours *behind* GMT. The ``tzstr`` time zone object will parse this as an
    offset 3 hours *ahead* of GMT. If you would like to maintain the POSIX
    behavior, pass a ``True`` value to ``posix_offset``.

    The :class:`tzrange` object provides the same functionality, but is
    specified using :class:`relativedelta.relativedelta` objects. rather than
    strings.

    :param s:
        A time zone string in ``TZ`` variable format. This can be a
        :class:`bytes` (2.x: :class:`str`), :class:`str` (2.x:
        :class:`unicode`) or a stream emitting unicode characters
        (e.g. :class:`StringIO`).

    :param posix_offset:
        Optional. If set to ``True``, interpret strings such as ``GMT+3`` or
        ``UTC+3`` as being 3 hours *behind* UTC rather than ahead, per the
        POSIX standard.

    .. caution::

        Prior to version 2.7.0, this function also supported time zones
        in the format:

            * ``EST5EDT,4,0,6,7200,10,0,26,7200,3600``
            * ``EST5EDT,4,1,0,7200,10,-1,0,7200,3600``

        This format is non-standard and has been deprecated; this function
        will raise a :class:`DeprecatedTZFormatWarning` until
        support is removed in a future version.

    .. _`GNU C Library: TZ Variable`:
        https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html
    """
    def __init__(self, s, posix_offset=False):
        global parser
        from dateutil.parser import _parser as parser

        self._s = s

        res = parser._parsetz(s)
        if res is None or res.any_unused_tokens:
            raise ValueError("unknown string format")

        # Here we break the compatibility with the TZ variable handling.
        # GMT-3 actually *means* the timezone -3.
        if res.stdabbr in ("GMT", "UTC") and not posix_offset:
            res.stdoffset *= -1

        # We must initialize it first, since _delta() needs
        # _std_offset and _dst_offset set. Use False in start/end
        # to avoid building it two times.
        tzrange.__init__(self, res.stdabbr, res.stdoffset,
                         res.dstabbr, res.dstoffset,
                         start=False, end=False)

        if not res.dstabbr:
            self._start_delta = None
            self._end_delta = None
        else:
            self._start_delta = self._delta(res.start)
            if self._start_delta:
                self._end_delta = self._delta(res.end, isend=1)

        self.hasdst = bool(self._start_delta)

    def _delta(self, x, isend=0):
        from dateutil import relativedelta
        kwargs = {}
        if x.month is not None:
            kwargs["month"] = x.month
            if x.weekday is not None:
                kwargs["weekday"] = relativedelta.weekday(x.weekday, x.week)
                if x.week > 0:
                    kwargs["day"] = 1
                else:
                    kwargs["day"] = 31
            elif x.day:
                kwargs["day"] = x.day
        elif x.yday is not None:
            kwargs["yearday"] = x.yday
        elif x.jyday is not None:
            kwargs["nlyearday"] = x.jyday
        if not kwargs:
            # Default is to start on first sunday of april, and end
            # on last sunday of october.
            if not isend:
                kwargs["month"] = 4
                kwargs["day"] = 1
                kwargs["weekday"] = relativedelta.SU(+1)
            else:
                kwargs["month"] = 10
                kwargs["day"] = 31
                kwargs["weekday"] = relativedelta.SU(-1)
        if x.time is not None:
            kwargs["seconds"] = x.time
        else:
            # Default is 2AM.
            kwargs["seconds"] = 7200
        if isend:
            # Convert to standard time, to follow the documented way
            # of working with the extra hour. See the documentation
            # of the tzinfo class.
            delta = self._dst_offset - self._std_offset
            kwargs["seconds"] -= delta.seconds + delta.days * 86400
        return relativedelta.relativedelta(**kwargs)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self._s))


class _tzicalvtzcomp(object):
    def __init__(self, tzoffsetfrom, tzoffsetto, isdst,
                 tzname=None, rrule=None):
        self.tzoffsetfrom = datetime.timedelta(seconds=tzoffsetfrom)
        self.tzoffsetto = datetime.timedelta(seconds=tzoffsetto)
        self.tzoffsetdiff = self.tzoffsetto - self.tzoffsetfrom
        self.isdst = isdst
        self.tzname = tzname
        self.rrule = rrule


class _tzicalvtz(_tzinfo):
    def __init__(self, tzid, comps=[]):
        super(_tzicalvtz, self).__init__()

        self._tzid = tzid
        self._comps = comps
        self._cachedate = []
        self._cachecomp = []
        self._cache_lock = _thread.allocate_lock()

    def _find_comp(self, dt):
        if len(self._comps) == 1:
            return self._comps[0]

        dt = dt.replace(tzinfo=None)

        try:
            with self._cache_lock:
                return self._cachecomp[self._cachedate.index(
                    (dt, self._fold(dt)))]
        except ValueError:
            pass

        lastcompdt = None
        lastcomp = None

        for comp in self._comps:
            compdt = self._find_compdt(comp, dt)

            if compdt and (not lastcompdt or lastcompdt < compdt):
                lastcompdt = compdt
                lastcomp = comp

        if not lastcomp:
            # RFC says nothing about what to do when a given
            # time is before the first onset date. We'll look for the
            # first standard component, or the first component, if
            # none is found.
            for comp in self._comps:
                if not comp.isdst:
                    lastcomp = comp
                    break
            else:
                lastcomp = comp[0]

        with self._cache_lock:
            self._cachedate.insert(0, (dt, self._fold(dt)))
            self._cachecomp.insert(0, lastcomp)

            if len(self._cachedate) > 10:
                self._cachedate.pop()
                self._cachecomp.pop()

        return lastcomp

    def _find_compdt(self, comp, dt):
        if comp.tzoffsetdiff < ZERO and self._fold(dt):
            dt -= comp.tzoffsetdiff

        compdt = comp.rrule.before(dt, inc=True)

        return compdt

    def utcoffset(self, dt):
        if dt is None:
            return None

        return self._find_comp(dt).tzoffsetto

    def dst(self, dt):
        comp = self._find_comp(dt)
        if comp.isdst:
            return comp.tzoffsetdiff
        else:
            return ZERO

    @tzname_in_python2
    def tzname(self, dt):
        return self._find_comp(dt).tzname

    def __repr__(self):
        return "<tzicalvtz %s>" % repr(self._tzid)

    __reduce__ = object.__reduce__


class tzical(object):
    """
    This object is designed to parse an iCalendar-style ``VTIMEZONE`` structure
    as set out in `RFC 5545`_ Section 4.6.5 into one or more `tzinfo` objects.

    :param `fileobj`:
        A file or stream in iCalendar format, which should be UTF-8 encoded
        with CRLF endings.

    .. _`RFC 5545`: https://tools.ietf.org/html/rfc5545
    """
    def __init__(self, fileobj):
        global rrule
        from dateutil import rrule

        if isinstance(fileobj, string_types):
            self._s = fileobj
            # ical should be encoded in UTF-8 with CRLF
            fileobj = open(fileobj, 'r')
        else:
            self._s = getattr(fileobj, 'name', repr(fileobj))
            fileobj = _nullcontext(fileobj)

        self._vtz = {}

        with fileobj as fobj:
            self._parse_rfc(fobj.read())

    def keys(self):
        """
        Retrieves the available time zones as a list.
        """
        return list(self._vtz.keys())

    def get(self, tzid=None):
        """
        Retrieve a :py:class:`datetime.tzinfo` object by its ``tzid``.

        :param tzid:
            If there is exactly one time zone available, omitting ``tzid``
            or passing :py:const:`None` value returns it. Otherwise a valid
            key (which can be retrieved from :func:`keys`) is required.

        :raises ValueError:
            Raised if ``tzid`` is not specified but there are either more
            or fewer than 1 zone defined.

        :returns:
            Returns either a :py:class:`datetime.tzinfo` object representing
            the relevant time zone or :py:const:`None` if the ``tzid`` was
            not found.
        """
        if tzid is None:
            if len(self._vtz) == 0:
                raise ValueError("no timezones defined")
            elif len(self._vtz) > 1:
                raise ValueError("more than one timezone available")
            tzid = next(iter(self._vtz))

        return self._vtz.get(tzid)

    def _parse_offset(self, s):
        s = s.strip()
        if not s:
            raise ValueError("empty offset")
        if s[0] in ('+', '-'):
            signal = (-1, +1)[s[0] == '+']
            s = s[1:]
        else:
            signal = +1
        if len(s) == 4:
            return (int(s[:2]) * 3600 + int(s[2:]) * 60) * signal
        elif len(s) == 6:
            return (int(s[:2]) * 3600 + int(s[2:4]) * 60 + int(s[4:])) * signal
        else:
            raise ValueError("invalid offset: " + s)

    def _parse_rfc(self, s):
        lines = s.splitlines()
        if not lines:
            raise ValueError("empty string")

        # Unfold
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            if not line:
                del lines[i]
            elif i > 0 and line[0] == " ":
                lines[i-1] += line[1:]
                del lines[i]
            else:
                i += 1

        tzid = None
        comps = []
        invtz = False
        comptype = None
        for line in lines:
            if not line:
                continue
            name, value = line.split(':', 1)
            parms = name.split(';')
            if not parms:
                raise ValueError("empty property name")
            name = parms[0].upper()
            parms = parms[1:]
            if invtz:
                if name == "BEGIN":
                    if value in ("STANDARD", "DAYLIGHT"):
                        # Process component
                        pass
                    else:
                        raise ValueError("unknown component: "+value)
                    comptype = value
                    founddtstart = False
                    tzoffsetfrom = None
                    tzoffsetto = None
                    rrulelines = []
                    tzname = None
                elif name == "END":
                    if value == "VTIMEZONE":
                        if comptype:
                            raise ValueError("component not closed: "+comptype)
                        if not tzid:
                            raise ValueError("mandatory TZID not found")
                        if not comps:
                            raise ValueError(
                                "at least one component is needed")
                        # Process vtimezone
                        self._vtz[tzid] = _tzicalvtz(tzid, comps)
                        invtz = False
                    elif value == comptype:
                        if not founddtstart:
                            raise ValueError("mandatory DTSTART not found")
                        if tzoffsetfrom is None:
                            raise ValueError(
                                "mandatory TZOFFSETFROM not found")
                        if tzoffsetto is None:
                            raise ValueError(
                                "mandatory TZOFFSETFROM not found")
                        # Process component
                        rr = None
                        if rrulelines:
                            rr = rrule.rrulestr("\n".join(rrulelines),
                                                compatible=True,
                                                ignoretz=True,
                                                cache=True)
                        comp = _tzicalvtzcomp(tzoffsetfrom, tzoffsetto,
                                              (comptype == "DAYLIGHT"),
                                              tzname, rr)
                        comps.append(comp)
                        comptype = None
                    else:
                        raise ValueError("invalid component end: "+value)
                elif comptype:
                    if name == "DTSTART":
                        # DTSTART in VTIMEZONE takes a subset of valid RRULE
                        # values under RFC 5545.
                        for parm in parms:
                            if parm != 'VALUE=DATE-TIME':
                                msg = ('Unsupported DTSTART param in ' +
                                       'VTIMEZONE: ' + parm)
                                raise ValueError(msg)
                        rrulelines.append(line)
                        founddtstart = True
                    elif name in ("RRULE", "RDATE", "EXRULE", "EXDATE"):
                        rrulelines.append(line)
                    elif name == "TZOFFSETFROM":
                        if parms:
                            raise ValueError(
                                "unsupported %s parm: %s " % (name, parms[0]))
                        tzoffsetfrom = self._parse_offset(value)
                    elif name == "TZOFFSETTO":
                        if parms:
                            raise ValueError(
                                "unsupported TZOFFSETTO parm: "+parms[0])
                        tzoffsetto = self._parse_offset(value)
                    elif name == "TZNAME":
                        if parms:
                            raise ValueError(
                                "unsupported TZNAME parm: "+parms[0])
                        tzname = value
                    elif name == "COMMENT":
                        pass
                    else:
                        raise ValueError("unsupported property: "+name)
                else:
                    if name == "TZID":
                        if parms:
                            raise ValueError(
                                "unsupported TZID parm: "+parms[0])
                        tzid = value
                    elif name in ("TZURL", "LAST-MODIFIED", "COMMENT"):
                        pass
                    else:
                        raise ValueError("unsupported property: "+name)
            elif name == "BEGIN" and value == "VTIMEZONE":
                tzid = None
                comps = []
                invtz = True

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self._s))


TZFILES = ["/etc/localtime", "localtime"]

def __get_gettz():
    tzlocal_classes = (tzlocal,)
    if tzwinlocal is not None:
        tzlocal_classes += (tzwinlocal,)

    class GettzFunc(object):
        """
        Retrieve a time zone object from a string representation

        This function is intended to retrieve the :py:class:`tzinfo` subclass
        that best represents the time zone that would be used if a POSIX
        `TZ variable`_ were set to the same value.

        If no argument or an empty string is passed to ``gettz``, local time
        is returned:

        .. code-block:: python3

            >>> gettz()
            tzfile('/etc/localtime')

        This function is also the preferred way to map IANA tz database keys
        to :class:`tzfile` objects. It searches for these keys in the
        following order:

        1. On the search path defined in :data:`TZPATH`.
        2. In the `tzdata <https://pypi.org/project/tzdata/>`_ Python package.
        3. Using the system-specific mechanisms (e.g. the Windows registry).

        .. code-block:: python3

            >>> gettz('Pacific/Kiritimati')
            tzfile('/usr/share/zoneinfo/Pacific/Kiritimati')

        On Windows, the standard is extended to include the Windows-specific
        zone names provided by the operating system:

        .. code-block:: python3

            >>> gettz('Egypt Standard Time')
            tzwin('Egypt Standard Time')

        Passing a GNU ``TZ`` style string time zone specification returns a
        :class:`tzstr` object:

        .. code-block:: python3

            >>> gettz('AEST-10AEDT-11,M10.1.0/2,M4.1.0/3')
            tzstr('AEST-10AEDT-11,M10.1.0/2,M4.1.0/3')

        :param name:
            A time zone name (IANA, or, on Windows, Windows keys), location of
            a ``tzfile(5)`` zoneinfo file or ``TZ`` variable style time zone
            specifier. An empty string, no argument or ``None`` is interpreted
            as local time.

        :return:
            Returns an instance of one of ``dateutil``'s :py:class:`tzinfo`
            subclasses.

        .. versionchanged:: 2.7.0

            After version 2.7.0, any two calls to ``gettz`` using the same
            input strings will return the same object:

            .. code-block:: python3

                >>> tz.gettz('America/Chicago') is tz.gettz('America/Chicago')
                True

            In addition to improving performance, this ensures that
            `"same zone" semantics`_ are used for datetimes in the same zone.


        .. _`TZ variable`:
            https://www.gnu.org/software/libc/manual/html_node/TZ-Variable.html

        .. _`"same zone" semantics`:
            https://blog.ganssle.io/articles/2018/02/aware-datetime-arithmetic.html
        """
        def __init__(self):

            self.__instances = weakref.WeakValueDictionary()
            self.__strong_cache_size = 8
            self.__strong_cache = OrderedDict()
            self._cache_lock = _thread.allocate_lock()

        def __call__(self, name=None):
            with self._cache_lock:
                rv = self.__instances.get(name, None)

                if rv is None:
                    # TODO: This holds the cache lock while nocache() reads
                    # the file, so a slow lookup (e.g. walking TZPATH on a
                    # network file system) blocks every other gettz call,
                    # including cache hits for unrelated keys.
                    rv = self.nocache(name=name)
                    if not (name is None
                            or isinstance(rv, tzlocal_classes)
                            or rv is None):
                        # tzlocal is slightly more complicated than the other
                        # time zone providers because it depends on environment
                        # at construction time, so don't cache that.
                        #
                        # We also cannot store weak references to None, so we
                        # will also not store that.
                        self.__instances[name] = rv
                    else:
                        # No need for strong caching, return immediately
                        return rv

                self.__strong_cache[name] = self.__strong_cache.pop(name, rv)

                if len(self.__strong_cache) > self.__strong_cache_size:
                    self.__strong_cache.popitem(last=False)

            return rv

        def set_cache_size(self, size):
            with self._cache_lock:
                self.__strong_cache_size = size
                while len(self.__strong_cache) > size:
                    self.__strong_cache.popitem(last=False)

        def cache_clear(self):
            with self._cache_lock:
                self.__instances = weakref.WeakValueDictionary()
                self.__strong_cache.clear()

        @staticmethod
        def nocache(name=None):
            """A non-cached version of gettz"""
            tz = None
            if not name:
                try:
                    name = os.environ["TZ"]
                except KeyError:
                    pass
            if name is None or name in ("", ":"):
                for filepath in TZFILES:
                    if not os.path.isabs(filepath):
                        filename = filepath
                        for path in _tzpath.TZPATH:
                            filepath = os.path.join(path, filename)
                            if _isfile(filepath):
                                break
                        else:
                            continue
                    if _isfile(filepath):
                        try:
                            tz = tzfile(filepath)
                            break
                        except (IOError, OSError, ValueError):
                            pass
                else:
                    tz = tzlocal()
            else:
                try:
                    if name.startswith(":"):
                        name = name[1:]
                except TypeError as e:
                    if isinstance(name, bytes):
                        new_msg = "gettz argument should be str, not bytes"
                        six.raise_from(TypeError(new_msg), e)
                    else:
                        raise

                # A NUL byte can never be part of a key or a path, and
                # depending on the platform and Python version it raises
                # ValueError from os.path, winreg or open(), so reject it
                # up front rather than catching it in every branch.
                if "\x00" in name:
                    return None

                if os.path.isabs(name):
                    if _isfile(name):
                        tz = tzfile(name)
                    else:
                        tz = None
                else:
                    if _escapes_tzpath(name):
                        _warn_tzpath_escape(name)

                    for path in _tzpath.TZPATH:
                        filepath = os.path.join(path, name)
                        if not _isfile(filepath):
                            filepath = filepath.replace(' ', '_')
                            if not _isfile(filepath):
                                continue
                        try:
                            tz = tzfile(filepath, key=name)
                            break
                        except (IOError, OSError, ValueError):
                            # TODO: A file that exists but can't be read or
                            # isn't a valid TZif file is silently skipped,
                            # and the key is looked up in the next TZPATH
                            # entry and then in tzdata. Consider warning
                            # here, since this usually means the system time
                            # zone data is broken.
                            pass
                    else:
                        tz = None
                        # As with the search path lookup above, also try
                        # the name with spaces replaced by underscores.
                        candidates = [name]
                        if " " in name:
                            candidates.append(name.replace(" ", "_"))

                        for candidate in candidates:
                            try:
                                with _tzdata_impl._load_tzdata(candidate) as f:
                                    return tzfile(f, key=name)
                            except ValueError:
                                # TZFileNotFound is a ValueError, and so is
                                # the error raised for files in tzdata that
                                # are not TZif files (e.g. "zone.tab"),
                                # which are skipped just as on TZPATH.
                                pass

                        if tzwin is not None:
                            try:
                                tz = tzwin(name)
                            except (WindowsError, UnicodeEncodeError):
                                # UnicodeEncodeError is for Python 2.7 compat
                                tz = None

                        if not tz:
                            for c in name:
                                # name is not a tzstr unless it has at least
                                # one offset. For short values of "name", an
                                # explicit for loop seems to be the fastest way
                                # To determine if a string contains a digit
                                if c in "0123456789":
                                    try:
                                        tz = tzstr(name)
                                    except ValueError:
                                        pass
                                    break
                            else:
                                if name in ("GMT", "UTC"):
                                    tz = UTC
                                elif name in time.tzname:
                                    tz = tzlocal()
            return tz

    return GettzFunc()


gettz = __get_gettz()
del __get_gettz


class DeprecatedTzKeyWarning(FutureWarning):
    """Warning raised when :func:`gettz` is given a key outside of TZPATH.

    Relative keys like ``"../../etc/localtime"`` resolve to files outside of
    every directory on :data:`TZPATH`. Support for these is deprecated, and a
    warnings filter turns this warning into an error by default. To keep the
    old behavior for now, filter it out, e.g.::

        warnings.filterwarnings(
            "ignore", category=dateutil.tz.DeprecatedTzKeyWarning
        )

    Absolute paths to TZif files are not affected.
    """


def _escapes_tzpath(name):
    # A relative key stays inside every TZPATH entry unless, once normalized
    # (which also turns os.altsep into os.sep), it starts by going up a
    # directory.
    return os.path.normpath(name).split(os.sep, 1)[0] == os.pardir


def _warn_tzpath_escape(name):
    # As in dateutil.zoneinfo.rebuild, the filter is appended at call time,
    # so any filter the user has installed for this category wins.
    warnings.filterwarnings(
        "error", category=DeprecatedTzKeyWarning, append=True
    )
    warnings.warn(
        "gettz(%r) refers to a file outside of TZPATH; support for keys "
        "like this is deprecated and will be removed in a future version. "
        "Use an absolute path instead." % (name,),
        DeprecatedTzKeyWarning,
        stacklevel=4,
    )


def available_iana_timezones():
    """Returns a set containing all available IANA time zones keys.

    These are suitable for use with :func:`gettz`. This is essentially a direct
    port of :py:func:`zoneinfo.available_timezones`.

    The search includes time zones found on :data:`TZPATH` as well as any
    time zones provided by the `tzdata <https://pypi.org/project/tzdata/>`_
    package if it is installed.

    :return:
        Returns a mutable set containing strings of time zones. Each call will
        return a fresh set.

    .. caution::

        This may attempt to open a large number of files, since the best way to
        determine if a given file on the time zone search path is to open it
        and check for the "magic string" at the beginning.

    .. note::

        These values are not designed to be exposed to end-users; for
        user-facing elements, applications should use something like CLDR (the
        Unicode Common Locale Data Repository) to get more user-friendly
        strings.
    """
    # Start with loading from the tzdata package if it exists: this has a
    # pre-assembled list of zones that only requires opening one file.
    try:
        valid_zones = set(_tzdata_impl._load_tzdata_keys())
    except ImportError:
        valid_zones = set()

    def valid_key(fpath):
        try:
            with open(fpath, "rb") as f:
                return f.read(4) == b"TZif"
        except Exception:  # pragma: nocover
            return False

    for tz_root in _tzpath.TZPATH:
        if not os.path.exists(tz_root):
            continue

        for root, dirnames, files in os.walk(tz_root):
            if root == tz_root:
                # right/ and posix/ are special directories and shouldn't be
                # included in the output of available zones
                if "right" in dirnames:
                    dirnames.remove("right")
                if "posix" in dirnames:
                    dirnames.remove("posix")

            for file in files:
                fpath = os.path.join(root, file)

                key = os.path.relpath(fpath, start=tz_root)
                if os.sep != "/":  # pragma: nocover
                    key = key.replace(os.sep, "/")

                if not key or key in valid_zones:
                    continue

                if valid_key(fpath):
                    valid_zones.add(key)

    if "posixrules" in valid_zones:
        # posixrules is a special symlink-only time zone where it exists, it
        # should not be included in the output
        valid_zones.remove("posixrules")
    if "localtime" in valid_zones:
        # localtime is a special symlink-only time zone where it exists, it
        # should not be included in the output
        valid_zones.remove("localtime")

    return valid_zones


def datetime_exists(dt, tz=None):
    """
    Given a datetime and a time zone, determine whether or not a given datetime
    would fall in a gap.

    :param dt:
        A :class:`datetime.datetime` (whose time zone will be ignored if ``tz``
        is provided.)

    :param tz:
        A :class:`datetime.tzinfo` with support for the ``fold`` attribute. If
        ``None`` or not provided, the datetime's own time zone will be used.

    :return:
        Returns a boolean value whether or not the "wall time" exists in
        ``tz``.

    .. versionadded:: 2.7.0
    """
    if tz is None:
        if dt.tzinfo is None:
            raise ValueError('Datetime is naive and no time zone provided.')
        tz = dt.tzinfo

    dt = dt.replace(tzinfo=None)

    # This is essentially a test of whether or not the datetime can survive
    # a round trip to UTC.
    dt_rt = dt.replace(tzinfo=tz).astimezone(UTC).astimezone(tz)
    dt_rt = dt_rt.replace(tzinfo=None)

    return dt == dt_rt


def datetime_ambiguous(dt, tz=None):
    """
    Given a datetime and a time zone, determine whether or not a given datetime
    is ambiguous (i.e if there are two times differentiated only by their DST
    status).

    :param dt:
        A :class:`datetime.datetime` (whose time zone will be ignored if ``tz``
        is provided.)

    :param tz:
        A :class:`datetime.tzinfo` with support for the ``fold`` attribute. If
        ``None`` or not provided, the datetime's own time zone will be used.

    :return:
        Returns a boolean value whether or not the "wall time" is ambiguous in
        ``tz``.

    .. versionadded:: 2.6.0
    """
    if tz is None:
        if dt.tzinfo is None:
            raise ValueError('Datetime is naive and no time zone provided.')

        tz = dt.tzinfo

    # If a time zone defines its own "is_ambiguous" function, we'll use that.
    is_ambiguous_fn = getattr(tz, 'is_ambiguous', None)
    if is_ambiguous_fn is not None:
        try:
            return tz.is_ambiguous(dt)
        except Exception:
            pass

    # If it doesn't come out and tell us it's ambiguous, we'll just check if
    # the fold attribute has any effect on this particular date and time.
    dt = dt.replace(tzinfo=tz)
    wall_0 = enfold(dt, fold=0)
    wall_1 = enfold(dt, fold=1)

    same_offset = wall_0.utcoffset() == wall_1.utcoffset()
    same_dst = wall_0.dst() == wall_1.dst()

    return not (same_offset and same_dst)


def resolve_imaginary(dt):
    """
    Given a datetime that may be imaginary, return an existing datetime.

    This function assumes that an imaginary datetime represents what the
    wall time would be in a zone had the offset transition not occurred, so
    it will always fall forward by the transition's change in offset.

    .. doctest::

        >>> from dateutil import tz
        >>> from datetime import datetime
        >>> NYC = tz.gettz('America/New_York')
        >>> print(tz.resolve_imaginary(datetime(2017, 3, 12, 2, 30, tzinfo=NYC)))
        2017-03-12 03:30:00-04:00

        >>> KIR = tz.gettz('Pacific/Kiritimati')
        >>> print(tz.resolve_imaginary(datetime(1995, 1, 1, 12, 30, tzinfo=KIR)))
        1995-01-02 12:30:00+14:00

    As a note, :func:`datetime.astimezone` is guaranteed to produce a valid,
    existing datetime, so a round-trip to and from UTC is sufficient to get
    an extant datetime, however, this generally "falls back" to an earlier time
    rather than falling forward to the STD side (though no guarantees are made
    about this behavior).

    :param dt:
        A :class:`datetime.datetime` which may or may not exist.

    :return:
        Returns an existing :class:`datetime.datetime`. If ``dt`` was not
        imaginary, the datetime returned is guaranteed to be the same object
        passed to the function.

    .. versionadded:: 2.7.0
    """
    if dt.tzinfo is not None and not datetime_exists(dt):

        curr_offset = (dt + datetime.timedelta(hours=24)).utcoffset()
        old_offset = (dt - datetime.timedelta(hours=24)).utcoffset()

        dt += curr_offset - old_offset

    return dt


def _datetime_to_timestamp(dt):
    """
    Convert a :class:`datetime.datetime` object to an epoch timestamp in
    seconds since January 1, 1970, ignoring the time zone.
    """
    return (dt.replace(tzinfo=None) - EPOCH).total_seconds()


if sys.version_info >= (3, 6):
    def _get_supported_offset(second_offset):
        return second_offset
else:
    def _get_supported_offset(second_offset):
        # For python pre-3.6, round to full-minutes if that's not the case.
        # Python's datetime doesn't accept sub-minute timezones. Check
        # http://python.org/sf/1447945 or https://bugs.python.org/issue5288
        # for some information.
        old_offset = second_offset
        calculated_offset = 60 * ((second_offset + 30) // 60)
        return calculated_offset


if sys.version_info < (3, 8):

    def _isfile(path):
        # bpo-33721: In Python 3.8 non-UTF8 paths return False rather than
        # raising an error. See https://bugs.python.org/issue33721
        try:
            return os.path.isfile(path)
        except ValueError:
            return False

else:
    _isfile = os.path.isfile


try:
    # Python 3.7 feature
    from contextlib import nullcontext as _nullcontext
except ImportError:
    class _nullcontext(object):
        """
        Class for wrapping contexts so that they are passed through in a
        with statement.
        """
        def __init__(self, context):
            self.context = context

        def __enter__(self):
            return self.context

        def __exit__(*args, **kwargs):
            pass

# vim:ts=4:sw=4:et
