import io
from itertools import chain
import os.path
import logging
from typing import Optional, List, Dict, Iterable, Any, overload, Iterator, TextIO, Tuple, MutableSequence

from .common import IntOrFloat
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .time import make_time, ms_to_str


class SSAFile(MutableSequence[SSAEvent]):
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

    DEFAULT_INFO: Dict[str, str] = {
        "WrapStyle": "0",
        "ScaledBorderAndShadow": "yes",
        "Collisions": "Normal"
    }

    def __init__(self) -> None:
        self.events: List[SSAEvent] = []  #: List of :class:`SSAEvent` instances, ie. individual subtitles.
        self.styles: Dict[str, SSAStyle] = {"Default": SSAStyle.DEFAULT_STYLE.copy()}  #: Dict of :class:`SSAStyle` instances.
        self.info: Dict[str, str] = self.DEFAULT_INFO.copy()  #: Dict with script metadata, ie. ``[Script Info]``.
        self.aegisub_project: Dict[str, str] = {}  #: Dict with Aegisub project, ie. ``[Aegisub Project Garbage]``.
        self.fonts_opaque: Dict[str, Any] = {}  #: Dict with embedded fonts, ie. ``[Fonts]``.
        self.graphics_opaque: Dict[str, Any] = {}  #: Dict with embedded images, ie. ``[Graphics]``.
        self.fps: Optional[float] = None  #: Framerate used when reading the file, if applicable.
        self.format: Optional[str] = None  #: Format of source subtitle file, if applicable, eg. ``"srt"``.

    # ------------------------------------------------------------------------
    # I/O methods
    # ------------------------------------------------------------------------

    @classmethod
    def load(cls, path: str, encoding: str = "utf-8", format_: Optional[str] = None, fps: Optional[float] = None,
             errors: Optional[str] = None, **kwargs: Any) -> "SSAFile":
        """
        Load subtitle file from given path.

        This method is implemented in terms of :meth:`SSAFile.from_file()`.

        See also:
            Specific formats may implement additional loading options,
            please refer to documentation of the implementation classes
            (eg. :meth:`pysubs2.formats.subrip.SubripFormat.from_file()`)

        Arguments:
            path (str): Path to subtitle file.
            encoding (str): Character encoding of input file.
                Defaults to UTF-8, you may need to change this.
            errors (Optional[str]): Error handling for character encoding
                of input file. Defaults to ``None``; use the value ``"surrogateescape"``
                for pass-through of bytes not supported by selected encoding via
                `Unicode surrogate pairs <https://en.wikipedia.org/wiki/Universal_Character_Set_characters#Surrogates>`_.
                See documentation of builtin ``open()`` function for more.

                .. versionchanged:: 1.7.0
                    The ``errors`` parameter was introduced to facilitate
                    pass-through of subtitle files with unknown text encoding.
                    Previous versions of the library behaved as if ``errors=None``.

            format_ (str): Optional, forces use of specific parser
                (eg. `"srt"`, `"ass"`). Otherwise, format is detected
                automatically from file contents. This argument should
                be rarely needed.
            fps (float): Framerate for frame-based formats (MicroDVD),
                for other formats this argument is ignored. Framerate might
                be detected from the file, in which case you don't need
                to specify it here (when given, this argument overrides
                autodetection).
            kwargs: Extra options for the reader.

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
            >>> subs2 = pysubs2.load("microdvd-subtitles.sub",fps=23.976)
            >>> subs3 = pysubs2.load("subrip-subtitles-with-fancy-tags.srt",keep_unknown_html_tags=True)

        """
        with open(path, encoding=encoding, errors=errors) as fp:
            return cls.from_file(fp, format_, fps=fps, **kwargs)

    @classmethod
    def from_string(cls, string: str, format_: Optional[str] = None, fps: Optional[float] = None,
                    **kwargs: Any) -> "SSAFile":
        """
        Load subtitle file from string.

        See :meth:`SSAFile.load()` for full description.

        Arguments:
            string (str): Subtitle file in a string. Note that the string must be Unicode (``str``, not ``bytes``).
            format_ (str): Optional, forces use of specific parser
                (eg. `"srt"`, `"ass"`). Otherwise, format is detected
                automatically from file contents. This argument should
                be rarely needed.
            fps (float): Framerate for frame-based formats (MicroDVD),
                for other formats this argument is ignored. Framerate might
                be detected from the file, in which case you don't need
                to specify it here (when given, this argument overrides
                autodetection).

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
    def from_file(cls, fp: TextIO, format_: Optional[str] = None, fps: Optional[float] = None,
                  **kwargs: Any) -> "SSAFile":
        """
        Read subtitle file from file object.

        See :meth:`SSAFile.load()` for full description.

        Note:
            This is a low-level method. Usually, one of :meth:`SSAFile.load()`
            or :meth:`SSAFile.from_string()` is preferable.

        Arguments:
            fp (file object): A file object, ie. :class:`TextIO` instance.
                Note that the file must be opened in text mode (as opposed to binary).
            format_ (str): Optional, forces use of specific parser
                (eg. `"srt"`, `"ass"`). Otherwise, format is detected
                automatically from file contents. This argument should
                be rarely needed.
            fps (float): Framerate for frame-based formats (MicroDVD),
                for other formats this argument is ignored. Framerate might
                be detected from the file, in which case you don't need
                to specify it here (when given, this argument overrides
                autodetection).

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

    def save(self, path: str, encoding: str = "utf-8", format_: Optional[str] = None, fps: Optional[float] = None,
             errors: Optional[str] = None, **kwargs: Any) -> None:
        """
        Save subtitle file to given path.

        This method is implemented in terms of :meth:`SSAFile.to_file()`.

        See also:
            Specific formats may implement additional saving options,
            please refer to documentation of the implementation classes
            (eg. :meth:`pysubs2.formats.subrip.SubripFormat.to_file()`)

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
            errors (Optional[str]): Error handling for character encoding
                of input file. Defaults to ``None``; use the value ``"surrogateescape"``
                for pass-through of bytes not supported by selected encoding via
                `Unicode surrogate pairs <https://en.wikipedia.org/wiki/Universal_Character_Set_characters#Surrogates>`_.
                See documentation of builtin ``open()`` function for more.

                .. versionchanged:: 1.7.0
                    The ``errors`` parameter was introduced to facilitate
                    pass-through of subtitle files with unknown text encoding.
                    Previous versions of the library behaved as if ``errors=None``.

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

        with open(path, "w", encoding=encoding, errors=errors) as fp:
            self.to_file(fp, format_, fps=fps, **kwargs)

    def to_string(self, format_: str, fps: Optional[float] = None, **kwargs: Any) -> str:
        """
        Get subtitle file as a string.

        See :meth:`SSAFile.save()` for full description.

        Returns:
            str

        """
        fp = io.StringIO()
        self.to_file(fp, format_, fps=fps, **kwargs)
        return fp.getvalue()

    def to_file(self, fp: TextIO, format_: str, fps: Optional[float] = None, **kwargs: Any) -> None:
        """
        Write subtitle file to file object.

        See :meth:`SSAFile.save()` for full description.

        Note:
            This is a low-level method. Usually, one of :meth:`SSAFile.save()`
            or :meth:`SSAFile.to_string()` is preferable.

        Arguments:
            fp (file object): A file object, ie. :class:`TextIO` instance.
                Note that the file must be opened in text mode (as opposed to binary).

        """
        impl = get_format_class(format_)
        impl.to_file(self, fp, format_, fps=fps, **kwargs)

    # ------------------------------------------------------------------------
    # Retiming subtitles
    # ------------------------------------------------------------------------

    def shift(self, h: IntOrFloat = 0, m: IntOrFloat = 0, s: IntOrFloat = 0, ms: IntOrFloat = 0,
              frames: Optional[int] = None, fps: Optional[float] = None) -> None:
        """
        Shift all subtitles by constant time amount.

        Shift may be time-based (the default) or frame-based. In the latter
        case, specify both frames and fps. h, m, s, ms will be ignored.

        Arguments:
            h: Integer or float values, may be positive or negative (hours).
            m: Integer or float values, may be positive or negative (minutes).
            s: Integer or float values, may be positive or negative (seconds).
            ms: Integer or float values, may be positive or negative (milliseconds).
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

    def transform_framerate(self, in_fps: float, out_fps: float) -> None:
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
            raise ValueError(f"Framerates must be positive, cannot transform {in_fps} -> {out_fps}")

        ratio = in_fps / out_fps
        for line in self:
            line.start = int(round(line.start * ratio))
            line.end = int(round(line.end * ratio))

    # ------------------------------------------------------------------------
    # Working with styles
    # ------------------------------------------------------------------------

    def rename_style(self, old_name: str, new_name: str) -> None:
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
        from .formats.substation import is_valid_field_content

        if old_name not in self.styles:
            raise KeyError(f"Style {old_name!r} not found")
        if new_name in self.styles:
            raise ValueError(f"There is already a style called {new_name!r}")
        if not is_valid_field_content(new_name):
            raise ValueError(f"{new_name!r} is not a valid name")

        self.styles[new_name] = self.styles[old_name]
        del self.styles[old_name]

        for line in self:
            # XXX also handle \r override tag
            if line.style == old_name:
                line.style = new_name

    def import_styles(self, subs: "SSAFile", overwrite: bool = True) -> None:
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

    def remove_miscellaneous_events(self) -> None:
        """
        Remove subtitles which appear to be non-essential (the --clean in CLI)

        Currently, this removes events matching any of these criteria:
        - SSA event type Comment
        - SSA drawing tags
        - Less than two characters of text
        - Duplicated text with identical time interval (only the first event is kept)
        """
        new_events = []

        duplicate_text_ids = set()
        times_to_texts: Dict[Tuple[int, int], List[str]] = {}
        for i, e in enumerate(self):
            tmp = times_to_texts.setdefault((e.start, e.end), [])
            if tmp.count(e.plaintext) > 0:
                duplicate_text_ids.add(i)
            tmp.append(e.plaintext)

        for i, e in enumerate(self):
            if e.is_drawing or e.is_comment:
                continue
            if len(e.plaintext.strip()) < 2:
                continue
            if i in duplicate_text_ids:
                continue

            new_events.append(e)

        self.events = new_events

    def get_text_events(self) -> List[SSAEvent]:
        """
        Return list of events excluding SSA comment lines and lines with SSA drawing tags
        """
        return [e for e in self if e.is_text]

    def equals(self, other: "SSAFile") -> bool:
        """
        Equality of two SSAFiles.

        Compares :attr:`SSAFile.info`, :attr:`SSAFile.styles` and :attr:`SSAFile.events`.
        Order of entries in OrderedDicts does not matter. "ScriptType" key in info is
        considered an implementation detail and thus ignored.

        Useful mostly in unit tests. Differences are logged at DEBUG level.

        """

        if isinstance(other, SSAFile):
            for key in set(chain(self.info.keys(), other.info.keys())) - {"ScriptType"}:
                self_info, other_info = self.info.get(key), other.info.get(key)
                if self_info is None:
                    logging.debug("%r missing in self.info", key)
                    return False
                elif other_info is None:
                    logging.debug("%r missing in other.info", key)
                    return False
                elif self_info != other_info:
                    logging.debug("info %r differs (self=%r, other=%r)", key, self_info, other_info)
                    return False

            for key in set(chain(self.fonts_opaque.keys(), other.fonts_opaque.keys())):
                self_font, other_font = self.fonts_opaque.get(key), other.fonts_opaque.get(key)
                if self_font is None:
                    logging.debug("%r missing in self.fonts_opaque", key)
                    return False
                elif other_font is None:
                    logging.debug("%r missing in other.fonts_opaque", key)
                    return False
                elif self_font != other_font:
                    logging.debug("fonts_opaque %r differs (self=%r, other=%r)", key, self_font, other_font)
                    return False

            for key in set(chain(self.graphics_opaque.keys(), other.graphics_opaque.keys())):
                self_image, other_image = self.graphics_opaque.get(key), other.graphics_opaque.get(key)
                if self_image is None:
                    logging.debug("%r missing in self.graphics_opaque", key)
                    return False
                elif other_image is None:
                    logging.debug("%r missing in other.graphics_opaque", key)
                    return False
                elif self_image != other_image:
                    logging.debug("graphics_opaque %r differs (self=%r, other=%r)", key, self_image, other_image)
                    return False

            for key in set(chain(self.styles.keys(), other.styles.keys())):
                self_style, other_style = self.styles.get(key), other.styles.get(key)
                if self_style is None:
                    logging.debug("%r missing in self.styles", key)
                    return False
                elif other_style is None:
                    logging.debug("%r missing in other.styles", key)
                    return False
                elif self_style != other_style:
                    for k in self_style.FIELDS:
                        if getattr(self_style, k) != getattr(other_style, k):
                            logging.debug("difference in field %r", k)
                    logging.debug("style %r differs (self=%r, other=%r)", key, self_style.as_dict(), other_style.as_dict())
                    return False

            if len(self) != len(other):
                logging.debug("different # of subtitles (self=%d, other=%d)", len(self), len(other))
                return False

            for i, (self_event, other_event) in enumerate(zip(self.events, other.events)):
                if not self_event.equals(other_event):
                    for k in self_event.FIELDS:
                        if getattr(self_event, k) != getattr(other_event, k):
                            logging.debug("difference in field %r", k)
                    logging.debug("event %d differs (self=%r, other=%r)", i, self_event.as_dict(), other_event.as_dict())
                    return False

            return True
        else:
            raise TypeError("Cannot compare to non-SSAFile object")

    def __repr__(self) -> str:
        if self.events:
            max_time = max(ev.end for ev in self)
            s = f"<SSAFile with {len(self)} events and {len(self.styles)} styles, last timestamp {ms_to_str(max_time)}>"
        else:
            s = f"<SSAFile with 0 events and {len(self.styles)} styles>"

        return s

    # ------------------------------------------------------------------------
    # MutableSequence implementation + sort()
    # ------------------------------------------------------------------------

    def sort(self) -> None:
        """Sort subtitles time-wise, in-place."""
        self.events.sort()

    def __iter__(self) -> Iterator[SSAEvent]:
        return iter(self.events)

    @overload
    def __getitem__(self, item: int) -> SSAEvent:
        pass

    @overload
    def __getitem__(self, s: slice) -> List[SSAEvent]:
        pass

    def __getitem__(self, item: Any) -> Any:
        return self.events[item]

    @overload
    def __setitem__(self, key: int, value: SSAEvent) -> None:
        pass

    @overload
    def __setitem__(self, keys: slice, values: Iterable[SSAEvent]) -> None:
        pass

    def __setitem__(self, key: Any, value: Any) -> None:
        if isinstance(key, int):
            if isinstance(value, SSAEvent):
                self.events[key] = value
            else:
                raise TypeError("SSAFile.events must contain only SSAEvent objects")
        elif isinstance(key, slice):
            values = list(value)
            if all(isinstance(v, SSAEvent) for v in values):
                self.events[key] = values
            else:
                raise TypeError("SSAFile.events must contain only SSAEvent objects")
        else:
            raise TypeError("Bad key type")

    @overload
    def __delitem__(self, key: int) -> None:
        pass

    @overload
    def __delitem__(self, s: slice) -> None:
        pass

    def __delitem__(self, key: Any) -> None:
        del self.events[key]

    def __len__(self) -> int:
        return len(self.events)

    def insert(self, index: int, value: SSAEvent) -> None:
        if isinstance(value, SSAEvent):
            self.events.insert(index, value)
        else:
            raise TypeError("SSAFile.events must contain only SSAEvent objects")


from .formats import autodetect_format, get_format_class, get_format_identifier  # noqa: E402
