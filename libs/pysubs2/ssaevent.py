from __future__ import unicode_literals
import re
from .time import ms_to_str, make_time
from .common import PY3


class SSAEvent(object):
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
    OVERRIDE_SEQUENCE = re.compile(r"{[^}]*}")

    #: All fields in SSAEvent.
    FIELDS = frozenset([
        "start", "end", "text", "marked", "layer", "style",
        "name", "marginl", "marginr", "marginv", "effect", "type"
    ])

    def __init__(self, **fields):
        self.start = 0 #: Subtitle start time (in milliseconds)
        self.end = 10000 #: Subtitle end time (in milliseconds)
        self.text = "" #: Text of subtitle (with SubStation override tags)
        self.marked = False #: (SSA only)
        self.layer = 0 #: Layer number, 0 is the lowest layer (ASS only)
        self.style = "Default" #: Style name
        self.name = "" #: Actor name
        self.marginl = 0 #: Left margin
        self.marginr = 0 #: Right margin
        self.marginv = 0 #: Vertical margin
        self.effect = "" #: Line effect
        self.type = "Dialogue" #: Line type (Dialogue/Comment)

        for k, v in fields.items():
            if k in self.FIELDS:
                setattr(self, k, v)
            else:
                raise ValueError("SSAEvent has no field named %r" % k)

    @property
    def duration(self):
        """
        Subtitle duration in milliseconds (read/write property).

        Writing to this property adjusts :attr:`SSAEvent.end`.
        Setting negative durations raises :exc:`ValueError`.
        """
        return self.end - self.start

    @duration.setter
    def duration(self, ms):
        if ms >= 0:
            self.end = self.start + ms
        else:
            raise ValueError("Subtitle duration cannot be negative")

    @property
    def is_comment(self):
        """
        When true, the subtitle is a comment, ie. not visible (read/write property).

        Setting this property is equivalent to changing
        :attr:`SSAEvent.type` to ``"Dialogue"`` or ``"Comment"``.
        """
        return self.type == "Comment"

    @is_comment.setter
    def is_comment(self, value):
        if value:
            self.type = "Comment"
        else:
            self.type = "Dialogue"

    @property
    def plaintext(self):
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
    def plaintext(self, text):
        self.text = text.replace("\n", r"\N")

    def shift(self, h=0, m=0, s=0, ms=0, frames=None, fps=None):
        """
        Shift start and end times.

        See :meth:`SSAFile.shift()` for full description.

        """
        delta = make_time(h=h, m=m, s=s, ms=ms, frames=frames, fps=fps)
        self.start += delta
        self.end += delta

    def copy(self):
        """Return a copy of the SSAEvent."""
        return SSAEvent(**self.as_dict())

    def as_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}

    def equals(self, other):
        """Field-based equality for SSAEvents."""
        if isinstance(other, SSAEvent):
            return self.as_dict() == other.as_dict()
        else:
            raise TypeError("Cannot compare to non-SSAEvent object")

    def __eq__(self, other):
        # XXX document this
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return self.start != other.start or self.end != other.end

    def __lt__(self, other):
        return (self.start, self.end) < (other.start, other.end)

    def __le__(self, other):
        return (self.start, self.end) <= (other.start, other.end)

    def __gt__(self, other):
        return (self.start, self.end) > (other.start, other.end)

    def __ge__(self, other):
        return (self.start, self.end) >= (other.start, other.end)

    def __repr__(self):
        s = "<SSAEvent type={self.type} start={start} end={end} text='{self.text}'>".format(
                self=self, start=ms_to_str(self.start), end=ms_to_str(self.end))
        if not PY3: s = s.encode("utf-8")
        return s
