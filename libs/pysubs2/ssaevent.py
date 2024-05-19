import re
import warnings
from typing import Optional, Dict, Any, ClassVar, FrozenSet
import dataclasses

from .common import IntOrFloat
from .time import ms_to_str, make_time


@dataclasses.dataclass(repr=False, eq=False, order=False)
class SSAEvent:
    """
    A SubStation Event, ie. one subtitle.

    In SubStation, each subtitle consists of multiple "fields" like Start, End and Text.
    These are exposed as attributes (note that they are lowercase; see :attr:`SSAEvent.FIELDS` for a list).
    Additionaly, there are some convenience properties like :attr:`SSAEvent.plaintext` or :attr:`SSAEvent.duration`.

    This class defines an ordering with respect to (start, end) timestamps.

    .. tip :: Use :func:`pysubs2.make_time()` to get times in milliseconds.

    Example::

        >>> ev = SSAEvent(start=make_time(s=1), end=make_time(s=2.5), text="Hello World!")

    """
    OVERRIDE_SEQUENCE: ClassVar = re.compile(r"{[^}]*}")

    start: int = 0  #: Subtitle start time (in milliseconds)
    end: int = 10000  #: Subtitle end time (in milliseconds)
    text: str = ""  #: Text of subtitle (with SubStation override tags)
    marked: bool = False  #: (SSA only)
    layer: int = 0  #: Layer number, 0 is the lowest layer (ASS only)
    style: str = "Default"  #: Style name
    name: str = ""  #: Actor name
    marginl: int = 0  #: Left margin
    marginr: int = 0  #: Right margin
    marginv: int = 0  #: Vertical margin
    effect: str = ""  #: Line effect
    type: str = "Dialogue"  #: Line type (Dialogue/Comment)

    @property
    def FIELDS(self) -> FrozenSet[str]:
        """All fields in SSAEvent."""
        warnings.warn("Deprecated in 1.2.0 - it's a dataclass now", DeprecationWarning)
        return frozenset(field.name for field in dataclasses.fields(self))

    @property
    def duration(self) -> IntOrFloat:
        """
        Subtitle duration in milliseconds (read/write property).

        Writing to this property adjusts :attr:`SSAEvent.end`.
        Setting negative durations raises :exc:`ValueError`.
        """
        return self.end - self.start

    @duration.setter
    def duration(self, ms: int) -> None:
        if ms >= 0:
            self.end = self.start + ms
        else:
            raise ValueError("Subtitle duration cannot be negative")

    @property
    def is_comment(self) -> bool:
        """
        When true, the subtitle is a comment, ie. not visible (read/write property).

        Setting this property is equivalent to changing
        :attr:`SSAEvent.type` to ``"Dialogue"`` or ``"Comment"``.
        """
        return self.type == "Comment"

    @is_comment.setter
    def is_comment(self, value: bool) -> None:
        if value:
            self.type = "Comment"
        else:
            self.type = "Dialogue"

    @property
    def is_drawing(self) -> bool:
        """Returns True if line is SSA drawing tag (ie. not text)"""
        from .formats.substation import parse_tags
        return any(sty.drawing for _, sty in parse_tags(self.text))

    @property
    def is_text(self) -> bool:
        """
        Returns False for SSA drawings and comment lines, True otherwise

        In general, for non-SSA formats these events should be ignored.
        """
        return not (self.is_comment or self.is_drawing)

    @property
    def plaintext(self) -> str:
        """
        Subtitle text as multi-line string with no tags (read/write property).

        Writing to this property replaces :attr:`SSAEvent.text` with given plain
        text. Newlines are converted to ``\\N`` tags.
        """
        text = self.text
        text = self.OVERRIDE_SEQUENCE.sub("", text)
        text = text.replace(r"\h", " ")
        text = text.replace(r"\n", "\n")
        text = text.replace(r"\N", "\n")
        return text

    @plaintext.setter
    def plaintext(self, text: str) -> None:
        self.text = text.replace("\n", r"\N")

    def shift(self, h: IntOrFloat = 0, m: IntOrFloat = 0, s: IntOrFloat = 0, ms: IntOrFloat = 0,
              frames: Optional[int] = None, fps: Optional[float] = None) -> None:
        """
        Shift start and end times.

        See :meth:`SSAFile.shift()` for full description.

        """
        delta = make_time(h=h, m=m, s=s, ms=ms, frames=frames, fps=fps)
        self.start += delta
        self.end += delta

    def copy(self) -> "SSAEvent":
        """Return a copy of the SSAEvent."""
        return SSAEvent(**self.as_dict())

    def as_dict(self) -> Dict[str, Any]:
        # dataclasses.asdict() would recursively dictify Color objects, which we don't want
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}

    def equals(self, other: "SSAEvent") -> bool:
        """Field-based equality for SSAEvents."""
        if isinstance(other, SSAEvent):
            return self.as_dict() == other.as_dict()
        else:
            raise TypeError("Cannot compare to non-SSAEvent object")

    def __eq__(self, other: object) -> bool:
        # XXX document this
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return self.start != other.start or self.end != other.end

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return (self.start, self.end) < (other.start, other.end)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return (self.start, self.end) <= (other.start, other.end)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return (self.start, self.end) > (other.start, other.end)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, SSAEvent):
            return NotImplemented
        return (self.start, self.end) >= (other.start, other.end)

    def __repr__(self) -> str:
        return f"<SSAEvent type={self.type} start={ms_to_str(self.start)} end={ms_to_str(self.end)} text={self.text!r}>"
