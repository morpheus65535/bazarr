from __future__ import print_function, unicode_literals, division
from collections import MutableSequence, OrderedDict
import io
from io import open
from itertools import starmap, chain
import os.path
import logging
from .formats import autodetect_format, get_format_class, get_format_identifier
from .substation import is_valid_field_content
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .time import make_time, ms_to_str
from .common import PY3


class SSAFile(MutableSequence):
    """
    Subtitle file in SubStation Alpha format.

    This class has a list-like interface which exposes :attr:`SSAFile.events`,
    list of subtitles in the file::

        subs = SSAFile.load("subtitles.srt")

        for line in subs:
            print(line.text)

        subs.insert(0, SSAEvent(start=0, end=make_time(s=2.5), text="New first subtitle"))

        del subs[0]

    """

    DEFAULT_INFO = OrderedDict([
        ("WrapStyle", "0"),
        ("ScaledBorderAndShadow", "yes"),
        ("Collisions", "Normal")])

    def __init__(self):
        self.events = [] #: List of :class:`SSAEvent` instances, ie. individual subtitles.
        self.styles = OrderedDict([("Default", SSAStyle.DEFAULT_STYLE.copy())]) #: Dict of :class:`SSAStyle` instances.
        self.info = self.DEFAULT_INFO.copy() #: Dict with script metadata, ie. ``[Script Info]``.
        self.aegisub_project = OrderedDict() #: Dict with Aegisub project, ie. ``[Aegisub Project Garbage]``.
        self.fps = None #: Framerate used when reading the file, if applicable.
        self.format = None #: Format of source subtitle file, if applicable, eg. ``"srt"``.

    # ------------------------------------------------------------------------
    # I/O methods
    # ------------------------------------------------------------------------

    @classmethod
    def load(cls, path, encoding="utf-8", format_=None, fps=None, **kwargs):
        """
        Load subtitle file from given path.

        Arguments:
            path (str): Path to subtitle file.
            encoding (str): Character encoding of input file.
                Defaults to UTF-8, you may need to change this.
            format_ (str): Optional, forces use of specific parser
                (eg. `"srt"`, `"ass"`). Otherwise, format is detected
                automatically from file contents. This argument should
                be rarely needed.
            fps (float): Framerate for frame-based formats (MicroDVD),
                for other formats this argument is ignored. Framerate might
                be detected from the file, in which case you don't need
                to specify it here (when given, this argument overrides
                autodetection).
            kwargs: Extra options for the parser.

        Returns:
            SSAFile

        Raises:
            IOError
            UnicodeDecodeError
            pysubs2.exceptions.UnknownFPSError
            pysubs2.exceptions.UnknownFormatIdentifierError
            pysubs2.exceptions.FormatAutodetectionError

        Note:
            pysubs2 may autodetect subtitle format and/or framerate. These
            values are set as :attr:`SSAFile.format` and :attr:`SSAFile.fps`
            attributes.

        Example:
            >>> subs1 = pysubs2.load("subrip-subtitles.srt")
            >>> subs2 = pysubs2.load("microdvd-subtitles.sub", fps=23.976)

        """
        with open(path, encoding=encoding) as fp:
            return cls.from_file(fp, format_, fps=fps, **kwargs)

    @classmethod
    def from_string(cls, string, format_=None, fps=None, **kwargs):
        """
        Load subtitle file from string.

        See :meth:`SSAFile.load()` for full description.

        Arguments:
            string (str): Subtitle file in a string. Note that the string
                must be Unicode (in Python 2).

        Returns:
            SSAFile

        Example:
            >>> text = '''
            ... 1
            ... 00:00:00,000 --> 00:00:05,000
            ... An example SubRip file.
            ... '''
            >>> subs = SSAFile.from_string(text)

        """
        fp = io.StringIO(string)
        return cls.from_file(fp, format_, fps=fps, **kwargs)

    @classmethod
    def from_file(cls, fp, format_=None, fps=None, **kwargs):
        """
        Read subtitle file from file object.

        See :meth:`SSAFile.load()` for full description.

        Note:
            This is a low-level method. Usually, one of :meth:`SSAFile.load()`
            or :meth:`SSAFile.from_string()` is preferable.

        Arguments:
            fp (file object): A file object, ie. :class:`io.TextIOBase` instance.
                Note that the file must be opened in text mode (as opposed to binary).

        Returns:
            SSAFile

        """
        if format_ is None:
            # Autodetect subtitle format, then read again using correct parser.
            # The file might be a pipe and we need to read it twice,
            # so just buffer everything.
            text = fp.read()
            fragment = text[:10000]
            format_ = autodetect_format(fragment)
            fp = io.StringIO(text)

        impl = get_format_class(format_)
        subs = cls() # an empty subtitle file
        subs.format = format_
        subs.fps = fps
        impl.from_file(subs, fp, format_, fps=fps, **kwargs)
        return subs

    def save(self, path, encoding="utf-8", format_=None, fps=None, **kwargs):
        """
        Save subtitle file to given path.

        Arguments:
            path (str): Path to subtitle file.
            encoding (str): Character encoding of output file.
                Defaults to UTF-8, which should be fine for most purposes.
            format_ (str): Optional, specifies desired subtitle format
                (eg. `"srt"`, `"ass"`). Otherwise, format is detected
                automatically from file extension. Thus, this argument
                is rarely needed.
            fps (float): Framerate for frame-based formats (MicroDVD),
                for other formats this argument is ignored. When omitted,
                :attr:`SSAFile.fps` value is used (ie. the framerate used
                for loading the file, if any). When the :class:`SSAFile`
                wasn't loaded from MicroDVD, or if you wish save it with
                different framerate, use this argument. See also
                :meth:`SSAFile.transform_framerate()` for fixing bad
                frame-based to time-based conversions.
            kwargs: Extra options for the writer.

        Raises:
            IOError
            UnicodeEncodeError
            pysubs2.exceptions.UnknownFPSError
            pysubs2.exceptions.UnknownFormatIdentifierError
            pysubs2.exceptions.UnknownFileExtensionError

        """
        if format_ is None:
            ext = os.path.splitext(path)[1].lower()
            format_ = get_format_identifier(ext)

        with open(path, "w", encoding=encoding) as fp:
            self.to_file(fp, format_, fps=fps, **kwargs)

    def to_string(self, format_, fps=None, **kwargs):
        """
        Get subtitle file as a string.

        See :meth:`SSAFile.save()` for full description.

        Returns:
            str

        """
        fp = io.StringIO()
        self.to_file(fp, format_, fps=fps, **kwargs)
        return fp.getvalue()

    def to_file(self, fp, format_, fps=None, **kwargs):
        """
        Write subtitle file to file object.

        See :meth:`SSAFile.save()` for full description.

        Note:
            This is a low-level method. Usually, one of :meth:`SSAFile.save()`
            or :meth:`SSAFile.to_string()` is preferable.

        Arguments:
            fp (file object): A file object, ie. :class:`io.TextIOBase` instance.
                Note that the file must be opened in text mode (as opposed to binary).

        """
        impl = get_format_class(format_)
        impl.to_file(self, fp, format_, fps=fps, **kwargs)

    # ------------------------------------------------------------------------
    # Retiming subtitles
    # ------------------------------------------------------------------------

    def shift(self, h=0, m=0, s=0, ms=0, frames=None, fps=None):
        """
        Shift all subtitles by constant time amount.

        Shift may be time-based (the default) or frame-based. In the latter
        case, specify both frames and fps. h, m, s, ms will be ignored.

        Arguments:
            h, m, s, ms: Integer or float values, may be positive or negative.
            frames (int): When specified, must be an integer number of frames.
                May be positive or negative. fps must be also specified.
            fps (float): When specified, must be a positive number.

        Raises:
            ValueError: Invalid fps or missing number of frames.

        """
        delta = make_time(h=h, m=m, s=s, ms=ms, frames=frames, fps=fps)
        for line in self:
            line.start += delta
            line.end += delta

    def transform_framerate(self, in_fps, out_fps):
        """
        Rescale all timestamps by ratio of in_fps/out_fps.

        Can be used to fix files converted from frame-based to time-based
        with wrongly assumed framerate.

        Arguments:
            in_fps (float)
            out_fps (float)

        Raises:
            ValueError: Non-positive framerate given.

        """
        if in_fps <= 0 or out_fps <= 0:
            raise ValueError("Framerates must be positive, cannot transform %f -> %f" % (in_fps, out_fps))

        ratio = in_fps / out_fps
        for line in self:
            line.start = int(round(line.start * ratio))
            line.end = int(round(line.end * ratio))

    # ------------------------------------------------------------------------
    # Working with styles
    # ------------------------------------------------------------------------

    def rename_style(self, old_name, new_name):
        """
        Rename a style, including references to it.

        Arguments:
            old_name (str): Style to be renamed.
            new_name (str): New name for the style (must be unused).

        Raises:
            KeyError: No style named old_name.
            ValueError: new_name is not a legal name (cannot use commas)
                or new_name is taken.

        """
        if old_name not in self.styles:
            raise KeyError("Style %r not found" % old_name)
        if new_name in self.styles:
            raise ValueError("There is already a style called %r" % new_name)
        if not is_valid_field_content(new_name):
            raise ValueError("%r is not a valid name" % new_name)

        self.styles[new_name] = self.styles[old_name]
        del self.styles[old_name]

        for line in self:
            # XXX also handle \r override tag
            if line.style == old_name:
                line.style = new_name

    def import_styles(self, subs, overwrite=True):
        """
        Merge in styles from other SSAFile.

        Arguments:
            subs (SSAFile): Subtitle file imported from.
            overwrite (bool): On name conflict, use style from the other file
                (default: True).

        """
        if not isinstance(subs, SSAFile):
            raise TypeError("Must supply an SSAFile.")

        for name, style in subs.styles.items():
            if name not in self.styles or overwrite:
                self.styles[name] = style

    # ------------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------------

    def equals(self, other):
        """
        Equality of two SSAFiles.

        Compares :attr:`SSAFile.info`, :attr:`SSAFile.styles` and :attr:`SSAFile.events`.
        Order of entries in OrderedDicts does not matter. "ScriptType" key in info is
        considered an implementation detail and thus ignored.

        Useful mostly in unit tests. Differences are logged at DEBUG level.

        """

        if isinstance(other, SSAFile):
            for key in set(chain(self.info.keys(), other.info.keys())) - {"ScriptType"}:
                sv, ov = self.info.get(key), other.info.get(key)
                if sv is None:
                    logging.debug("%r missing in self.info", key)
                    return False
                elif ov is None:
                    logging.debug("%r missing in other.info", key)
                    return False
                elif sv != ov:
                    logging.debug("info %r differs (self=%r, other=%r)", key, sv, ov)
                    return False

            for key in set(chain(self.styles.keys(), other.styles.keys())):
                sv, ov = self.styles.get(key), other.styles.get(key)
                if sv is None:
                    logging.debug("%r missing in self.styles", key)
                    return False
                elif ov is None:
                    logging.debug("%r missing in other.styles", key)
                    return False
                elif sv != ov:
                    for k in sv.FIELDS:
                        if getattr(sv, k) != getattr(ov, k): logging.debug("difference in field %r", k)
                    logging.debug("style %r differs (self=%r, other=%r)", key, sv.as_dict(), ov.as_dict())
                    return False

            if len(self) != len(other):
                logging.debug("different # of subtitles (self=%d, other=%d)", len(self), len(other))
                return False

            for i, (se, oe) in enumerate(zip(self.events, other.events)):
                if not se.equals(oe):
                    for k in se.FIELDS:
                        if getattr(se, k) != getattr(oe, k): logging.debug("difference in field %r", k)
                    logging.debug("event %d differs (self=%r, other=%r)", i, se.as_dict(), oe.as_dict())
                    return False

            return True
        else:
            raise TypeError("Cannot compare to non-SSAFile object")

    def __repr__(self):
        if self.events:
            max_time = max(ev.end for ev in self)
            s = "<SSAFile with %d events and %d styles, last timestamp %s>" % \
                    (len(self), len(self.styles), ms_to_str(max_time))
        else:
            s = "<SSAFile with 0 events and %d styles>" % len(self.styles)

        if not PY3: s = s.encode("utf-8")
        return s

    # ------------------------------------------------------------------------
    # MutableSequence implementation + sort()
    # ------------------------------------------------------------------------

    def sort(self):
        """Sort subtitles time-wise, in-place."""
        self.events.sort()

    def __getitem__(self, item):
        return self.events[item]

    def __setitem__(self, key, value):
        if isinstance(value, SSAEvent):
            self.events[key] = value
        else:
            raise TypeError("SSAFile.events must contain only SSAEvent objects")

    def __delitem__(self, key):
        del self.events[key]

    def __len__(self):
        return len(self.events)

    def insert(self, index, value):
        if isinstance(value, SSAEvent):
            self.events.insert(index, value)
        else:
            raise TypeError("SSAFile.events must contain only SSAEvent objects")
