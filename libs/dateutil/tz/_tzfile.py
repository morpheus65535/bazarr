# -*- coding: utf-8 -*-
import bisect
import calendar
import functools
import io
import os
import re
import stat
import struct
import sys
from datetime import MAXYEAR, MINYEAR, datetime, timedelta

import six

from ._common import _tzinfo, enfold, tzname_in_python2

EPOCH = datetime(1970, 1, 1)
EPOCHORDINAL = EPOCH.toordinal()

# TODO: Move this to _common.py
try:
    # Python 3.7 feature
    from contextlib import nullcontext as _nullcontext
except ImportError:
    import contextlib

    @contextlib.contextmanager
    def _nullcontext(context):
        yield context


# It is relatively expensive to construct new timedelta objects, and in most
# cases we're looking at the same deltas, like integer numbers of hours, etc.
# To improve speed and memory use, we'll keep a dictionary with references
# to the ones we've already used so far.
#
# Loading every time zone in the 2020a version of the time zone database
# requires 447 timedeltas, which requires approximately the amount of space
# that ZoneInfo("America/New_York") with 236 transitions takes up, so we will
# set the cache size to 512 so that in the common case we always get cache
# hits, but specifically crafted ZoneInfo objects don't leak arbitrary amounts
# of memory.
_TIMEDELTA_CACHE_SIZE = 512
if six.PY2:

    def _cache_load_timedelta(f):
        from collections import OrderedDict

        from six.moves import _thread

        CACHE_LOCK = _thread.allocate_lock()
        TIMEDELTA_CACHE = OrderedDict()

        @functools.wraps(f)
        def cached_load_timedelta(seconds):
            # OrderedDict is implemented in Python on Python 2, so every
            # access has to hold the lock to keep its linked list intact.
            with CACHE_LOCK:
                rv = TIMEDELTA_CACHE.pop(seconds, None)
                if rv is None:
                    rv = f(seconds)

                TIMEDELTA_CACHE[seconds] = rv

                if len(TIMEDELTA_CACHE) > _TIMEDELTA_CACHE_SIZE:
                    TIMEDELTA_CACHE.popitem(last=False)

            return rv

        return cached_load_timedelta

else:
    _cache_load_timedelta = functools.lru_cache(maxsize=512)


@_cache_load_timedelta
def _load_timedelta(seconds):
    return timedelta(seconds=seconds)


def _unpickle(cls, key, filename, data):
    obj = cls.__new__(cls)
    obj._key = key
    obj._filename = filename

    obj._load_from_data(data)

    return obj


class tzfile(_tzinfo):
    """
    This is a ``tzinfo`` subclass that allows one to use the ``tzfile(5)``
    format timezone files to extract current and historical zone information.

    :param fileobj:
        This can be an opened file stream or a file name that the time zone
        information can be read from.

    :param filename:
        This is an optional parameter specifying the source of the time zone
        information in the event that ``fileobj`` is a file object. If omitted
        and ``fileobj`` is a file stream, this parameter will be set either to
        ``fileobj``'s ``name`` attribute or to ``repr(fileobj)``.

    This class is intended to be mostly equivalent to the standard library
    :py:class:`zoneinfo.ZoneInfo` class. The primary differences are:

        * All caching in ``tzfile`` is handled by :func:`tz.gettz` level (you
          should generally not attempt to construct a ``tzfile`` directly).
        * ``tzfile`` objects are pickled by value rather than by reference to
          the IANA key.
        * ``tzfile`` has equality-by-value semantics, whereas
          :py:class:`~zoneinfo.ZoneInfo` has equality-by-identity semantics.

    See `Sources for Time Zone and Daylight Saving Time Data
    <https://data.iana.org/time-zones/tz-link.html>`_ for more information.
    Time zone files can be compiled from the `IANA Time Zone database files
    <https://www.iana.org/time-zones>`_ with the `zic time zone compiler
    <https://www.freebsd.org/cgi/man.cgi?query=zic&sektion=8>`_

    .. note::

        Only construct a ``tzfile`` directly if you have a specific timezone
        file on disk that you want to read into a Python ``tzinfo`` object.
        If you want to get a ``tzfile`` representing a specific IANA zone,
        (e.g. ``'America/New_York'``), you should call
        :func:`dateutil.tz.gettz` with the zone identifier.

    .. versionchanged:: 3.0.0
        ``tzfile`` is now a partial backport of :py:class:`zoneinfo.ZoneInfo`,
        which brings with it support for Version 2 and 3 ``tzfile(5)`` binaries.

    **Examples:**

    Using the US Eastern time zone as an example, we can see that a ``tzfile``
    provides time zone information for the standard Daylight Saving offsets:

    .. testsetup:: tzfile

        from dateutil.tz import gettz
        from datetime import datetime

    .. doctest:: tzfile

        >>> NYC = gettz('America/New_York')
        >>> NYC
        tzfile('/usr/share/zoneinfo/America/New_York')

        >>> print(datetime(2016, 1, 3, tzinfo=NYC))     # EST
        2016-01-03 00:00:00-05:00

        >>> print(datetime(2016, 7, 7, tzinfo=NYC))     # EDT
        2016-07-07 00:00:00-04:00


    The ``tzfile`` structure contains a fully history of the time zone,
    so historical dates will also have the right offsets. For example, before
    the adoption of standard time on November 18, 1883, New York used local
    mean time:

    .. doctest:: tzfile

       >>> print(datetime(1883, 11, 18, tzinfo=NYC))    # LMT
       1883-11-18 00:00:00-04:56:02

    Python versions before 3.6 do not support sub-minute offsets, so there the
    offset is rounded to ``-04:56``.

    And during World War II, New York was on "Eastern War Time", which was a
    state of permanent daylight saving time:

    .. doctest:: tzfile

        >>> print(datetime(1944, 2, 7, tzinfo=NYC))    # EWT
        1944-02-07 00:00:00-04:00

    """

    def __init__(self, fileobj, filename=None, key=None):
        super(tzfile, self).__init__()

        file_opened_here = False
        if isinstance(fileobj, six.string_types):
            self._filename = fileobj
            fileobj = open(fileobj, "rb")
            file_opened_here = True
        elif filename is not None:
            self._filename = filename
        elif hasattr(fileobj, "name"):
            self._filename = fileobj.name
        elif key is not None:
            self._filename = key
        else:
            self._filename = repr(fileobj)

        if fileobj is not None:
            if not file_opened_here:
                fileobj = _nullcontext(fileobj)

            with fileobj as file_stream:
                self._load_file(file_stream)

        self._key = key

    @property
    def key(self):
        """
        Read-only attribute returning the ``key`` constructor argument.

        For zones generated from :func:`gettz`, this will be the IANA key
        passed to ``gettz`` — no normalization is done, so although in most
        distributions of the time zone database "US/Eastern" is a link to
        "America/New_York", ``tz.gettz("US/Eastern").key`` should always return
        ``"US/Eastern"``.

        For zones constructed via another mechanism without specifying ``key``,
        this returns :obj:`None`.
        """
        return self._key

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
        return self._is_ambiguous_or_imaginary(dt) == 1

    def _is_ambiguous_or_imaginary(self, dt):
        if dt is None or self._fixed_offset:
            return 0

        timestamp = self._get_local_timestamp(dt)
        tti_0 = self._find_trans(dt, fold=0, timestamp=timestamp)
        tti_1 = self._find_trans(dt, fold=1, timestamp=timestamp)

        # Returns 1 if ambiguous, -1 if imaginary and 0 otherwise.
        return int(tti_0.utcoff > tti_1.utcoff) - int(
            tti_1.utcoff > tti_0.utcoff
        )

    def utcoffset(self, dt):
        return self._find_trans(dt).utcoff

    def dst(self, dt):
        return self._find_trans(dt).dstoff

    @tzname_in_python2
    def tzname(self, dt):
        return self._find_trans(dt).tzname

    def fromutc(self, dt):
        """
        The ``tzfile`` implementation of :py:func:`datetime.tzinfo.fromutc`.

        :param dt:
            A :py:class:`datetime.datetime` object.

        :raises TypeError:
            Raised if ``dt`` is not a :py:class:`datetime.datetime` object.

        :raises ValueError:
            Raised if this is called with a ``dt`` which does not have this
            ``tzinfo`` attached.

        :return:
            Returns a :py:class:`datetime.datetime` object representing the
            wall time in ``self``'s time zone.
        """

        if not isinstance(dt, datetime):
            raise TypeError("fromutc() requires a datetime argument")
        if dt.tzinfo is not self:
            raise ValueError("dt.tzinfo is not self")

        timestamp = self._get_local_timestamp(dt)
        num_trans = len(self._trans_utc)

        if num_trans >= 1 and timestamp < self._trans_utc[0]:
            tti = self._tti_before
            fold = 0
        elif (
            num_trans == 0 or timestamp > self._trans_utc[-1]
        ) and not isinstance(self._tz_after, _ttinfo):
            tti, fold = self._tz_after.get_trans_info_fromutc(
                timestamp, dt.year
            )

            # The TZ string only knows about its own transitions, so check
            # whether we are in a fold created by the last explicit one.
            if num_trans and not fold:
                if num_trans > 1:
                    tti_prev = self._ttinfos[-2]
                else:
                    tti_prev = self._tti_before

                shift = tti_prev.utcoff - tti.utcoff
                fold = shift.total_seconds() > timestamp - self._trans_utc[-1]
        elif num_trans == 0:
            tti = self._tz_after
            fold = 0
        else:
            idx = bisect.bisect_right(self._trans_utc, timestamp)

            if num_trans > 1 and timestamp >= self._trans_utc[1]:
                tti_prev, tti = self._ttinfos[idx - 2 : idx]
            elif timestamp > self._trans_utc[-1]:
                # Only reachable with exactly one transition, so the
                # offset before it is _tti_before, not _ttinfos[-1].
                tti_prev = self._tti_before
                tti = self._tz_after
            else:
                tti_prev = self._tti_before
                tti = self._ttinfos[0]

            # Detect fold
            shift = tti_prev.utcoff - tti.utcoff
            fold = shift.total_seconds() > timestamp - self._trans_utc[idx - 1]
        dt += tti.utcoff
        if fold:
            return enfold(dt, fold=1)
        else:
            return dt

    def _find_trans(self, dt, fold=None, timestamp=None):
        if dt is None:
            if self._fixed_offset:
                return self._tz_after
            else:
                return _NO_TTINFO

        if timestamp is None:
            ts = self._get_local_timestamp(dt)
        else:
            ts = timestamp

        if fold is None:
            fold = getattr(dt, "fold", 0)

        lt = self._trans_local[fold]

        num_trans = len(lt)

        if num_trans and ts < lt[0]:
            return self._tti_before
        elif not num_trans or ts > lt[-1]:
            if isinstance(self._tz_after, _TZStr):
                tti = self._tz_after.get_trans_info(ts, dt.year, fold)

                # The TZ string only describes times after the last explicit
                # transition. If its answer for this local time is a different
                # offset from the last transition's, and corresponds to a time
                # before that transition (e.g. when the TZ string's own DST
                # period for that year ends after the transition), the offset
                # from the last explicit transition applies instead.
                last_tti = self._ttinfos[-1] if num_trans else None
                if (
                    last_tti is not None
                    and tti.utcoff != last_tti.utcoff
                    and ts - tti.utcoff.total_seconds() < self._trans_utc[-1]
                ):
                    return last_tti

                return tti
            else:
                return self._tz_after
        else:
            # idx is the transition that occurs after this timestamp, so we
            # subtract off 1 to get the current ttinfo
            idx = bisect.bisect_right(lt, ts) - 1
            assert idx >= 0
            return self._ttinfos[idx]

    def _get_local_timestamp(self, dt):
        return (
            (dt.toordinal() - EPOCHORDINAL) * 86400
            + dt.hour * 3600
            + dt.minute * 60
            + dt.second
        )

    # The attributes set by _unpickle and _load_from_data
    _UNPICKLE_ATTRS = frozenset(
        [
            "_filename",
            "_fixed_offset",
            "_isdst",
            "_key",
            "_trans_idx",
            "_trans_local",
            "_trans_utc",
            "_tti_before",
            "_ttinfo_list",
            "_ttinfos",
            "_tz_after",
            "_tz_str",
            "_utcoff_raw",
        ]
    )

    def __reduce__(self):
        return self.__reduce_ex__(None)

    def __reduce_ex__(self, protocol):
        utcoff = [
            int(ttinfo.utcoff.total_seconds()) for ttinfo in self._ttinfo_list
        ]
        utcoff = getattr(self, "_utcoff_raw", utcoff)
        abbr = [ttinfo.tzname for ttinfo in self._ttinfo_list]

        # dst() is inferred per transition, so the transitions don't map back
        # to the local time types, and these are kept as they were in the file
        trans_idx = self._trans_idx
        isdst = self._isdst

        trans_utc = self._trans_utc
        tz_str = self._tz_str

        data = (trans_idx, trans_utc, utcoff, isdst, abbr, tz_str)
        args = (self.__class__, self._key, self._filename, data)

        # Preserve any other instance state, such as attributes added by a
        # subclass, but not the attributes that _unpickle rebuilds from data
        state = {
            k: v for k, v in vars(self).items() if k not in self._UNPICKLE_ATTRS
        }
        if state:
            return (_unpickle, args, state)

        return (_unpickle, args)

    def _load_file(self, fobj):
        # Reading the file requires seeking past the parts we don't use and
        # reading the footer a line at a time, so read anything that doesn't
        # support that (e.g. a pipe) into memory first; TZif files are small.
        if not _is_seekable(fobj) or not hasattr(fobj, "readline"):
            fobj = io.BytesIO(fobj.read())

        # Retrieve all the data as it exists in the zoneinfo file
        data = load_data(fobj)
        self._load_from_data(data)

    def _load_from_data(self, data):
        trans_idx, trans_utc, utcoff, isdst, abbr, tz_str = data

        # Infer the DST offsets (needed for .dst()) from the data, for each
        # transition and for each local time type
        trans_dstoff = self._utcoff_to_dstoff(
            trans_idx, trans_utc, utcoff, isdst
        )
        dstoff = [3600 if dst else 0 for dst in isdst]
        for idx, trans_off in zip(trans_idx, trans_dstoff):
            dstoff[idx] = trans_off

        if sys.version_info < (3, 6):
            # For python pre-3.6, round to full-minutes if that's not the case.
            # Python's datetime doesn't accept sub-minute timezones. Check
            # http://python.org/sf/1447945 or https://bugs.python.org/issue5288
            # for some information.
            utcoff_adjusted = [60 * ((s + 30) // 60) for s in utcoff]
            dstoff = [60 * ((s + 30) // 60) for s in dstoff]
            trans_dstoff = [60 * ((s + 30) // 60) for s in trans_dstoff]
            self._utcoff_raw = utcoff
        else:
            utcoff_adjusted = utcoff

        # Convert all the transition times (UTC) into "seconds since 1970-01-01 local time"
        trans_local = self._ts_to_local(trans_idx, trans_utc, utcoff_adjusted)

        # Construct `_ttinfo` objects for each transition in the file
        _ttinfo_list = [
            _ttinfo(
                _load_timedelta(utcoffset), _load_timedelta(dstoffset), tzname
            )
            for utcoffset, dstoffset, tzname in zip(
                utcoff_adjusted, dstoff, abbr
            )
        ]

        self._ttinfo_list = _ttinfo_list

        self._trans_idx = trans_idx
        self._isdst = isdst
        self._trans_utc = trans_utc
        self._trans_local = trans_local

        # Transitions to the same local time type usually have the same DST
        # offset, so share the _ttinfo objects between them where possible.
        ttinfos = {}
        self._ttinfos = []
        for idx, trans_off in zip(trans_idx, trans_dstoff):
            tti = _ttinfo_list[idx]
            if tti.dstoff.total_seconds() != trans_off:
                key = (idx, trans_off)
                if key not in ttinfos:
                    ttinfos[key] = _ttinfo(
                        tti.utcoff, _load_timedelta(trans_off), tti.tzname
                    )
                tti = ttinfos[key]
            self._ttinfos.append(tti)

        # Find the first non-DST transition
        for i in range(len(isdst)):
            if not isdst[i]:
                self._tti_before = _ttinfo_list[i]
                break
        else:
            if self._ttinfos:
                self._tti_before = self._ttinfos[0]
            else:
                self._tti_before = None

        # Set the "fallback" time zone
        self._tz_str = tz_str
        if tz_str is not None and tz_str != b"":
            self._tz_after = _parse_tz_str(tz_str.decode())
        else:
            if not self._ttinfos and not _ttinfo_list:
                raise ValueError("No time zone information found.")

            if self._ttinfos:
                self._tz_after = self._ttinfos[-1]
            else:
                # With no transitions and no TZ string, RFC 9636 Section 3.2
                # says that local time is specified by time type 0
                self._tz_after = _ttinfo_list[0]

        # Determine if this is a "fixed offset" zone, meaning that the output
        # of the utcoffset, dst and tzname functions does not depend on the
        # specific datetime passed.
        #
        # We make three simplifying assumptions here:
        #
        # 1. If _tz_after is not a _ttinfo, it has transitions that might
        #    actually occur (it is possible to construct TZ strings that
        #    specify STD and DST but no transitions ever occur, such as
        #    AAA0BBB,0/0,J365/25).
        # 2. If _ttinfo_list contains more than one _ttinfo object, the objects
        #    represent different offsets.
        # 3. _ttinfo_list contains no unused _ttinfos (in which case an
        #    otherwise fixed-offset zone with extra _ttinfos defined may
        #    appear to *not* be a fixed offset zone).
        #
        # Violations to these assumptions would be fairly exotic, and exotic
        # zones should almost certainly not be used with datetime.time (the
        # only thing that would be affected by this).
        if len(_ttinfo_list) > 1 or not isinstance(self._tz_after, _ttinfo):
            self._fixed_offset = False
        elif not _ttinfo_list:
            self._fixed_offset = True
        else:
            self._fixed_offset = _ttinfo_list[0] == self._tz_after

    @staticmethod
    def _utcoff_to_dstoff(trans_idx, trans_utc, utcoffsets, isdsts):
        """Infer the DST offset (the value of dst()) for each transition.

        TZif files give the total UTC offset of each local time type and
        whether it is DST, but not how much of the offset is DST, so this has
        to be worked out from the standard time on either side of each DST
        period. That is done for each transition rather than for each local
        time type, because zic reuses a local time type for periods with
        different standard offsets (e.g. UTC+0 DST in the Azores was double
        summer time in the 1940s and summer time later).
        """
        n = len(trans_idx)

        # The DST offset implied by the last standard time before and the
        # first standard time after each transition. Before the first
        # transition, it's the first standard time type, as for _tti_before.
        first_std_utcoff = next(
            (utcoff for utcoff, dst in zip(utcoffsets, isdsts) if not dst),
            None,
        )
        before = [None] * n
        after = [None] * n
        for indices, implied, std_utcoff in (
            (range(n), before, first_std_utcoff),
            (range(n - 1, -1, -1), after, None),
        ):
            for i in indices:
                idx = trans_idx[i]
                if not isdsts[idx]:
                    std_utcoff = utcoffsets[idx]
                elif std_utcoff is not None:
                    implied[i] = utcoffsets[idx] - std_utcoff

        # DST offsets where the standard time is the same on both sides
        clear_cut = [
            (trans_utc[i], before[i])
            for i in range(n)
            if before[i] and before[i] == after[i]
        ]

        dstoffs = [0] * n
        for i in range(n):
            if not isdsts[trans_idx[i]]:
                continue

            candidates = {c for c in (before[i], after[i]) if c}
            if len(candidates) > 1:
                # The standard offset changed during the DST period. A change
                # from local mean time can give something like 0:34:39, which
                # is not a plausible amount of DST.
                plausible = {c for c in candidates if c % 300 == 0}
                candidates = plausible or candidates

            if len(candidates) > 1:
                # Prefer the amount of DST the zone used around the same
                # time, e.g. Tehran used 1:00 and Rarotonga 0:30, though the
                # TZif data for Tehran in 1977 and for Rarotonga in 1978 look
                # the same. This has to be local in time, because some zones
                # used different amounts in different eras (e.g. Montevideo
                # used 0:30 in the 1920s and 1:00 later).
                nearby = {
                    dstoff
                    for ts, dstoff in clear_cut
                    if abs(ts - trans_utc[i]) <= _DST_CONSENSUS_WINDOW
                }
                consensus = candidates & nearby
                if len(consensus) == 1:
                    candidates = consensus

            if candidates:
                # Otherwise, prefer positive DST, then the smaller amount. In
                # the 1942 occupation zones, e.g. Europe/Kyiv, the standard
                # time before gives -1:00 and the one after +1:00.
                dstoffs[i] = min(candidates, key=lambda c: (c < 0, abs(c)))
            else:
                # Without any standard time to compare to, one hour is a much
                # better guess than 0
                dstoffs[i] = 3600

        return dstoffs

    @staticmethod
    def _ts_to_local(trans_idx, trans_list_utc, utcoffsets):
        """Generate number of seconds since 1970 *in the local time*.

        This is necessary to easily find the transition times in local time"""
        if not trans_list_utc:
            return [[], []]

        # Start with the timestamps and modify in-place
        trans_list_wall = [list(trans_list_utc), list(trans_list_utc)]

        if len(utcoffsets) > 1:
            offset_0 = utcoffsets[0]
            offset_1 = utcoffsets[trans_idx[0]]
            if offset_1 > offset_0:
                offset_1, offset_0 = offset_0, offset_1
        else:
            offset_0 = offset_1 = utcoffsets[0]

        trans_list_wall[0][0] += offset_0
        trans_list_wall[1][0] += offset_1

        for i in range(1, len(trans_idx)):
            offset_0 = utcoffsets[trans_idx[i - 1]]
            offset_1 = utcoffsets[trans_idx[i]]

            if offset_1 > offset_0:
                offset_1, offset_0 = offset_0, offset_1

            trans_list_wall[0][i] += offset_0
            trans_list_wall[1][i] += offset_1

        return trans_list_wall

    def __eq__(self, other):
        if not isinstance(other, tzfile):
            return NotImplemented

        return (
            self._trans_utc == other._trans_utc
            and self._trans_local == other._trans_local
            and self._ttinfos == other._ttinfos
            and self._tti_before == other._tti_before
            and self._fallback_key() == other._fallback_key()
        )

    def _fallback_key(self):
        # The behavior after the last transition is determined either by the
        # TZ string or, in its absence, by a single _ttinfo; _TZStr objects
        # do not define equality, so compare the string they came from.
        if isinstance(self._tz_after, _ttinfo):
            return self._tz_after
        return self._tz_str

    __hash__ = None

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self._filename))


# Before Python 3.16, pipes on Windows claim to be seekable, but seeking on
# them silently does nothing. See https://github.com/python/cpython/issues/86768
_SEEKABLE_PIPES_BUG = sys.platform == "win32" and sys.version_info < (3, 16)


def _is_seekable(fobj):
    if not hasattr(fobj, "seek"):
        return False

    seekable = getattr(fobj, "seekable", None)
    # Python 2 file objects can seek but have no seekable() method
    if seekable is not None and not seekable():
        return False

    if not _SEEKABLE_PIPES_BUG:
        return True

    # For anything backed by a file descriptor, only trust regular files.
    try:
        fd = fobj.fileno()
    except (AttributeError, OSError, ValueError):
        # io.UnsupportedOperation (e.g. from BytesIO) is both of the latter
        return True

    try:
        return stat.S_ISREG(os.fstat(fd).st_mode)
    except OSError:
        return True


def load_data(fobj):
    try:
        return _load_data(fobj)
    except struct.error as e:
        # struct.unpack fails when a read comes up short
        six.raise_from(
            ValueError("Invalid TZif file: unexpected end of file"), e
        )


def _load_data(fobj):
    header = _TZifHeader.from_file(fobj)

    if header.version == 1:
        time_size = 4
        time_type = "l"
    else:
        # Version 2+ has 64-bit integer transition times
        time_size = 8
        time_type = "q"

        # Version 2+ also starts with a Version 1 header and data, which
        # we need to skip now
        skip_bytes = (
            header.timecnt * 5  # Transition times and types
            + header.typecnt * 6  # Local time type records
            + header.charcnt  # Time zone designations
            + header.leapcnt * 8  # Leap second records
            + header.isstdcnt  # Standard/wall indicators
            + header.isutcnt  # UT/local indicators
        )

        fobj.seek(skip_bytes, 1)

        # Now we need to read the second header, which is not the same
        # as the first
        header = _TZifHeader.from_file(fobj)

    typecnt = header.typecnt
    timecnt = header.timecnt
    charcnt = header.charcnt

    # The data portion starts with timecnt transitions and indices
    if timecnt:
        trans_list_utc = struct.unpack(
            ">%s%s" % (timecnt, time_type), fobj.read(timecnt * time_size)
        )
        trans_idx = struct.unpack(">%sB" % timecnt, fobj.read(timecnt))

        if max(trans_idx) >= typecnt:
            raise ValueError(
                "Invalid transition index found while reading TZif: %s"
                % max(trans_idx)
            )
    else:
        trans_list_utc = ()
        trans_idx = ()

    # Read the ttinfo struct, (utoff, isdst, abbrind)
    if typecnt:
        utcoff, isdst, abbrind = zip(
            *(struct.unpack(">lbb", fobj.read(6)) for i in range(typecnt))
        )
    else:
        utcoff = ()
        isdst = ()
        abbrind = ()

    # Now read the abbreviations. They are null-terminated strings, indexed
    # not by position in the array but by position in the unsplit
    # abbreviation string. I suppose this makes more sense in C, which uses
    # null to terminate the strings, but it's inconvenient here...
    abbr_vals = {}
    abbr_chars = fobj.read(charcnt)

    def get_abbr(idx):
        # Gets a string starting at idx and running until the next \x00
        #
        # We cannot pre-populate abbr_vals by splitting on \x00 because there
        # are some zones that use subsets of longer abbreviations, like so:
        #
        #  LMT\x00AHST\x00HDT\x00
        #
        # Where the idx to abbr mapping should be:
        #
        # {0: "LMT", 4: "AHST", 5: "HST", 9: "HDT"}
        if idx not in abbr_vals:
            span_end = abbr_chars.find(b"\x00", idx)
            abbr_vals[idx] = abbr_chars[idx:span_end].decode()

        return abbr_vals[idx]

    abbr = tuple(get_abbr(idx) for idx in abbrind)

    # The remainder of the file consists of leap seconds (currently unused) and
    # the standard/wall and ut/local indicators, which are metadata we don't need.
    # In version 2 files, we need to skip the unnecessary data to get at the TZ string,
    # and in version 1 files we'll just hopefully consume the rest of the file.

    # Each leap second record has size (time_size + 4)
    skip_bytes = (
        header.isutcnt + header.isstdcnt + header.leapcnt * (time_size + 4)
    )
    fobj.seek(skip_bytes, 1)
    if header.version >= 2:
        c = fobj.read(1)  # Should be \n
        if c != b"\n":
            raise ValueError("Invalid TZif file: expected newline, got %r" % c)

        line = fobj.readline()
        if not line.endswith(b"\n"):
            raise ValueError("Invalid TZif file: unexpected end of file")
        tz_str = line.rstrip(b"\n")
    else:
        tz_str = None

    return trans_idx, trans_list_utc, utcoff, isdst, abbr, tz_str


# How close in time (in seconds) the DST periods that _utcoff_to_dstoff uses
# to choose between two possible DST offsets have to be
_DST_CONSENSUS_WINDOW = 10 * 365 * 86400


class _TZifHeader(object):
    __slots__ = [
        "version",
        "isutcnt",
        "isstdcnt",
        "leapcnt",
        "timecnt",
        "typecnt",
        "charcnt",
    ]

    def __init__(self, *args):
        assert len(self.__slots__) == len(args)
        for attr, val in zip(self.__slots__, args):
            setattr(self, attr, val)

    @classmethod
    def from_file(cls, stream):
        # The header starts with a 4-byte "magic" value
        if stream.read(4) != b"TZif":
            raise ValueError("Invalid TZif file: magic not found")

        _version = stream.read(1)
        if _version == b"\x00":
            version = 1
        else:
            version = int(_version)
        stream.read(15)

        args = (version,)

        # Slots are defined in the order that the bytes are arranged
        args = args + struct.unpack(">6l", stream.read(24))

        return cls(*args)


class _ttinfo(object):
    __slots__ = ["utcoff", "dstoff", "tzname"]

    def __init__(self, utcoff, dstoff, tzname):
        self.utcoff = utcoff
        self.dstoff = dstoff
        self.tzname = tzname

    def __eq__(self, other):
        if not isinstance(other, _ttinfo):
            return NotImplemented

        return (
            self.utcoff == other.utcoff
            and self.dstoff == other.dstoff
            and self.tzname == other.tzname
        )

    def __ne__(self, other):
        # Python 2 does not derive __ne__ from __eq__
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return eq
        return not eq

    def __repr__(self):  # pragma: nocover
        return "%s(%s, %s, %s)" % (
            self.__class__.__name__,
            self.utcoff,
            self.dstoff,
            self.tzname,
        )


_NO_TTINFO = _ttinfo(None, None, None)


def _unpack(t):
    # Python 2-specific backport for x, *y = t
    return t[0], t[1:]


# re.ASCII does not exist on Python 2, where str patterns are ASCII-only
# anyway (and unicode patterns are too unless re.UNICODE is passed).
_RE_ASCII = getattr(re, "ASCII", 0)


def _fullmatch(pattern, string, flags=0):
    # Python 2-specific backport of re.fullmatch
    return re.match(r"(?:%s)\Z" % pattern, string, flags)


def _round_offset(seconds):
    # Python < 3.6 does not support sub-minute offsets, see the comment in
    # tzfile._load_from_data.
    if sys.version_info < (3, 6):
        return 60 * ((seconds + 30) // 60)
    return seconds


def _parse_tz_str(tz_str):
    # The tz string has the format:
    #
    # std[offset[dst[offset],start[/time],end[/time]]]
    #
    # std and dst must be 3 or more characters long and must not contain
    # a leading colon, embedded digits, commas, nor a plus or minus signs;
    # The spaces between "std" and "offset" are only for display and are
    # not actually present in the string.
    #
    # The format of the offset is ``[+|-]hh[:mm[:ss]]``

    # TODO: When we drop Python 2, this should be offset_str, *start_end_str = ...
    offset_str, start_end_str = _unpack(tz_str.split(",", 1))

    parser_re = (
        r"(?P<std>[a-zA-Z]+|<[a-zA-Z0-9+-]+>)"
        r"(?:"
        r"(?P<stdoff>[+-]?\d{1,3}(?::\d{2}(?::\d{2})?)?)"
        r"(?:"
        r"(?P<dst>[a-zA-Z]+|<[a-zA-Z0-9+-]+>)"
        r"(?P<dstoff>[+-]?\d{1,3}(?::\d{2}(?::\d{2})?)?)?"
        r")?"  # dst
        r")?"  # stdoff
    )

    m = _fullmatch(parser_re, offset_str, _RE_ASCII)

    if m is None:
        raise ValueError("%s is not a valid TZ string" % tz_str)

    std_abbr = m.group("std")
    dst_abbr = m.group("dst")
    dst_offset = None

    std_abbr = std_abbr.strip("<>")

    if dst_abbr:
        dst_abbr = dst_abbr.strip("<>")

    std_offset = m.group("stdoff")
    if std_offset:
        try:
            std_offset = _round_offset(_parse_tz_delta(std_offset))
        except ValueError as e:
            raise ValueError("Invalid STD offset in %s" % tz_str)
    else:
        # The STD offset is required
        raise ValueError("Invalid STD offset in %s" % tz_str)

    if dst_abbr is not None:
        dst_offset = m.group("dstoff")
        if dst_offset:
            try:
                dst_offset = _round_offset(_parse_tz_delta(dst_offset))
            except ValueError as e:
                raise ValueError("Invalid DST offset in %s" % tz_str)
        else:
            dst_offset = std_offset + 3600

        if not start_end_str:
            raise ValueError("Missing transition rules: %s" % tz_str)

        start_end_strs = start_end_str[0].split(",", 1)
        try:
            start, end = (_parse_dst_start_end(x) for x in start_end_strs)
        except ValueError as e:
            raise ValueError("Invalid TZ string: %s" % tz_str)

        return _TZStr(std_abbr, std_offset, dst_abbr, dst_offset, start, end)
    elif start_end_str:
        raise ValueError("Transition rule present without DST: %s" % tz_str)
    else:
        # This is a static ttinfo, don't return _TZStr
        return _ttinfo(
            _load_timedelta(std_offset), _load_timedelta(0), std_abbr
        )


def _parse_dst_start_end(dststr):
    date, time = _unpack(dststr.split("/", 1))
    date_type = date[:1]
    if date_type == "M":
        n_is_julian = False
        m = _fullmatch(r"M(\d{1,2})\.(\d)\.(\d)", date, _RE_ASCII)
        if m is None:
            raise ValueError("Invalid dst start/end date: %s" % dststr)
        date_offset = tuple(map(int, m.groups()))
        offset = _CalendarOffset(*date_offset)
    else:
        if date_type == "J":
            n_is_julian = True
            date = date[1:]
        else:
            n_is_julian = False

        if _fullmatch(r"\d{1,3}", date, _RE_ASCII) is None:
            raise ValueError("Invalid dst start/end date: %s" % dststr)
        doy = int(date)
        offset = _DayOffset(doy, n_is_julian)

    if time:
        offset.hour, offset.minute, offset.second = _parse_transition_time(
            time[0]
        )

    return offset


def _parse_transition_time(time_str):
    match = _fullmatch(
        r"(?P<sign>[+-])?(?P<h>\d{1,3})(:(?P<m>\d{2})(:(?P<s>\d{2}))?)?",
        time_str,
        _RE_ASCII,
    )
    if match is None:
        raise ValueError("Invalid time: %s" % time_str)

    h, m, s = (int(v or 0) for v in map(match.group, ("h", "m", "s")))

    if h > 167:
        raise ValueError("Hour must be in [0, 167]: %s" % time_str)

    if match.group("sign") == "-":
        h, m, s = -h, -m, -s

    return h, m, s


def _parse_tz_delta(tz_delta):
    match = _fullmatch(
        r"(?P<sign>[+-])?(?P<h>\d{1,3})(:(?P<m>\d{2})(:(?P<s>\d{2}))?)?",
        tz_delta,
        _RE_ASCII,
    )
    # Anything passed to this function should already have hit an equivalent
    # regular expression to find the section to parse.
    assert match is not None, tz_delta

    h, m, s = (int(v or 0) for v in map(match.group, ("h", "m", "s")))

    total = h * 3600 + m * 60 + s

    if h > 24:
        raise ValueError("Offset hours must be in [0, 24]: %s" % tz_delta)

    # Yes, +5 maps to an offset of -5h
    if match.group("sign") != "-":
        total *= -1

    return total


class _TZStr(object):
    __slots__ = (
        "std",
        "dst",
        "start",
        "end",
        "get_trans_info",
        "get_trans_info_fromutc",
        "dst_diff",
    )

    def __init__(
        self, std_abbr, std_offset, dst_abbr, dst_offset, start=None, end=None
    ):
        self.dst_diff = dst_offset - std_offset
        std_offset = _load_timedelta(std_offset)
        self.std = _ttinfo(
            utcoff=std_offset, dstoff=_load_timedelta(0), tzname=std_abbr
        )

        self.start = start
        self.end = end

        dst_offset = _load_timedelta(dst_offset)
        delta = _load_timedelta(self.dst_diff)
        self.dst = _ttinfo(utcoff=dst_offset, dstoff=delta, tzname=dst_abbr)

        # These are assertions because the constructor should only be called
        # by functions that would fail before passing start or end
        assert start is not None, "No transition start specified"
        assert end is not None, "No transition end specified"

        self.get_trans_info = self._get_trans_info
        self.get_trans_info_fromutc = self._get_trans_info_fromutc

    def transitions(self, year):
        start = self.start.year_to_epoch(year)
        end = self.end.year_to_epoch(year)
        return start, end

    def _near_new_year(self, ts, year):
        """Whether ts is close enough to the new year that the rules for the
        previous or next year might matter."""
        year_start = _post_epoch_days_before_year(year) * 86400
        year_end = _post_epoch_days_before_year(year + 1) * 86400
        return (
            ts < year_start + _NEW_YEAR_MARGIN
            or ts >= year_end - _NEW_YEAR_MARGIN
        )

    def _get_trans_info(self, ts, year, fold):
        """Get the information about the current transition - tti"""
        if self._near_new_year(ts, year):
            return self._get_trans_info_near_new_year(ts, fold)

        start, end = self.transitions(year)

        # With fold = 0, the period (denominated in local time) with the
        # smaller offset starts at the end of the gap and ends at the end of
        # the fold; with fold = 1, it runs from the start of the gap to the
        # beginning of the fold.
        #
        # So in order to determine the DST boundaries we need to know both
        # the fold and whether DST is positive or negative (rare), and it
        # turns out that this boils down to fold XOR is_positive.
        if fold == (self.dst_diff >= 0):
            end -= self.dst_diff
        else:
            start += self.dst_diff

        if start < end:
            isdst = start <= ts < end
        else:
            isdst = not (end <= ts < start)

        return self.dst if isdst else self.std

    def _get_trans_info_near_new_year(self, ts, fold):
        # Answer the question in terms of UTC, where the transitions from the
        # adjacent years are taken into account: a local time is valid for
        # an offset if the rules give that offset at the corresponding UTC
        # time.
        valid = []
        for tti in (self.std, self.dst):
            utc_ts = ts - tti.utcoff.total_seconds()
            try:
                utc_year = (EPOCH + timedelta(seconds=utc_ts)).year
            except OverflowError:
                # Before year 1 or after year 9999
                utc_year = MINYEAR if utc_ts < 0 else MAXYEAR
            actual, _ = self._get_trans_info_fromutc_near_new_year(
                utc_ts, utc_year
            )
            if actual is tti:
                valid.append(tti)

        if len(valid) == 1:
            return valid[0]

        smaller, larger = sorted((self.std, self.dst), key=lambda t: t.utcoff)
        if valid:
            # Ambiguous: fold=0 is the first occurrence, with the larger offset
            return larger if fold == 0 else smaller
        else:
            # Imaginary: fold=0 uses the offset from before the transition
            return smaller if fold == 0 else larger

    def _get_trans_info_fromutc_near_new_year(self, ts, year):
        # The rules are in terms of the local year, which near the new year
        # is not always the UTC year, and a rule can put a transition up to a
        # week into the previous or next year (e.g. "J365/25"), so look at the
        # transitions for the years on either side as well and use the last
        # one before ts.
        std_utcoff = self.std.utcoff.total_seconds()
        dst_utcoff = self.dst.utcoff.total_seconds()

        transitions = []
        for y in (year - 1, year, year + 1):
            start, end = self.transitions(y)
            transitions.append((start - std_utcoff, True))
            transitions.append((end - dst_utcoff, False))

        # When one DST period ends at the same instant as the next one starts,
        # as with "DST all year" rules like "0/0,J365/25", sorting puts the
        # end first, so these stay in DST without a transition in between.
        transitions.sort()

        isdst = not transitions[0][1]
        last_change = None
        i = 0
        while i < len(transitions) and transitions[i][0] <= ts:
            trans_ts = transitions[i][0]
            new_isdst = isdst
            while i < len(transitions) and transitions[i][0] == trans_ts:
                new_isdst = transitions[i][1]
                i += 1

            if new_isdst != isdst:
                isdst = new_isdst
                last_change = trans_ts

        if isdst:
            tti, tti_prev = self.dst, self.std
        else:
            tti, tti_prev = self.std, self.dst

        # A transition to a smaller offset creates a fold just after it.
        fold = False
        if last_change is not None:
            shift = (tti_prev.utcoff - tti.utcoff).total_seconds()
            fold = shift > ts - last_change

        return (tti, fold)

    def _get_trans_info_fromutc(self, ts, year):
        if self._near_new_year(ts, year):
            return self._get_trans_info_fromutc_near_new_year(ts, year)

        start, end = self.transitions(year)
        start -= self.std.utcoff.total_seconds()
        end -= self.dst.utcoff.total_seconds()

        if start < end:
            isdst = start <= ts < end
        else:
            isdst = not (end <= ts < start)

        # For positive DST, the ambiguous period is one dst_diff after the end
        # of DST; for negative DST, the ambiguous period is one dst_diff before
        # the start of DST.
        if self.dst_diff > 0:
            ambig_start = end
            ambig_end = end + self.dst_diff
        else:
            ambig_start = start
            ambig_end = start - self.dst_diff

        fold = ambig_start <= ts < ambig_end

        return (self.dst if isdst else self.std, fold)


# A rule can put a transition up to 167 hours (just under a week) away from
# the day it names, and local time is at most a day or so away from UTC, so
# only times within this distance of the new year can be affected by the
# rules for the previous or next year.
_NEW_YEAR_MARGIN = 10 * 86400


def _post_epoch_days_before_year(year):
    """Get the number of days between 1970-01-01 and YEAR-01-01"""
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400 + 1 - EPOCHORDINAL


class _DayOffset(object):
    __slots__ = ["d", "julian", "hour", "minute", "second"]

    def __init__(self, d, julian, hour=2, minute=0, second=0):
        min_day = 0 + julian  # convert bool to int
        if not min_day <= d <= 365:
            raise ValueError("d must be in [%s, 365], not: %s" % (min_day, d))

        self.d = d
        self.julian = julian
        self.hour = hour
        self.minute = minute
        self.second = second

    def year_to_epoch(self, year):
        days_before_year = _post_epoch_days_before_year(year)

        # "n" counts days from 0 and includes February 29; "Jn" counts days
        # from 1 and never counts February 29, so in leap years, J60 (March 1)
        # and every day after it is one day later than its number suggests.
        d = self.d
        if self.julian:
            d -= 1
            if d >= 59 and calendar.isleap(year):
                d += 1

        epoch = (days_before_year + d) * 86400
        epoch += self.hour * 3600 + self.minute * 60 + self.second

        return epoch


class _CalendarOffset(object):
    __slots__ = ["m", "w", "d", "hour", "minute", "second"]

    _DAYS_BEFORE_MONTH = (
        -1,
        0,
        31,
        59,
        90,
        120,
        151,
        181,
        212,
        243,
        273,
        304,
        334,
    )

    def __init__(self, m, w, d, hour=2, minute=0, second=0):
        if not 1 <= m <= 12:
            raise ValueError("m must be in [1, 12]")

        if not 1 <= w <= 5:
            raise ValueError("w must be in [1, 5]")

        if not 0 <= d <= 6:
            raise ValueError("d must be in [0, 6]")

        self.m = m
        self.w = w
        self.d = d
        self.hour = hour
        self.minute = minute
        self.second = second

    @classmethod
    def _ymd2ord(cls, year, month, day):
        return (
            _post_epoch_days_before_year(year)
            + cls._DAYS_BEFORE_MONTH[month]
            + (month > 2 and calendar.isleap(year))
            + day
            - 1
        )

    # TODO: These are not actually epoch dates as they are expressed in local time
    def year_to_epoch(self, year):
        """Calculates the datetime of the occurrence from the year"""
        # We know year and month, we need to convert w, d into day of month
        #
        # Week 1 is the first week in which day `d` (where 0 = Sunday) appears.
        # Week 5 represents the last occurrence of day `d`, so we need to know
        # the range of the month.
        #
        # This doesn't use calendar.monthrange because the rules for years 0
        # and 10000 can affect times that datetime can represent, and
        # calendar.monthrange constructs a datetime.date. Instead, get the
        # weekday (0 = Monday) from the ordinal: 1970-01-01 was a Thursday.
        first_ordinal = self._ymd2ord(year, self.m, 1)
        first_day = (first_ordinal + 3) % 7
        if self.m == 12:
            next_ordinal = self._ymd2ord(year + 1, 1, 1)
        else:
            next_ordinal = self._ymd2ord(year, self.m + 1, 1)
        days_in_month = next_ordinal - first_ordinal

        # This equation seems magical, so I'll break it down:
        # 1. calendar says 0 = Monday, POSIX says 0 = Sunday
        #    so we need first_day + 1 to get 1 = Monday -> 7 = Sunday,
        #    which is still equivalent because this math is mod 7
        # 2. Get first day - desired day mod 7: -1 % 7 = 6, so we don't need
        #    to do anything to adjust negative numbers.
        # 3. Add 1 because month days are a 1-based index.
        month_day = (self.d - (first_day + 1)) % 7 + 1

        # Now use a 0-based index version of `w` to calculate the w-th
        # occurrence of `d`
        month_day += (self.w - 1) * 7

        # month_day will only be > days_in_month if w was 5, and `w` means
        # "last occurrence of `d`", so now we just check if we over-shot the
        # end of the month and if so knock off 1 week.
        if month_day > days_in_month:
            month_day -= 7

        ordinal = self._ymd2ord(year, self.m, month_day)
        epoch = ordinal * 86400
        epoch += self.hour * 3600 + self.minute * 60 + self.second
        return epoch
