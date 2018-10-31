from __future__ import unicode_literals
from .common import Color, PY3


class SSAStyle(object):
    """
    A SubStation Style.

    In SubStation, each subtitle (:class:`SSAEvent`) is associated with a style which defines its font, color, etc.
    Like a subtitle event, a style also consists of "fields"; see :attr:`SSAStyle.FIELDS` for a list
    (note the spelling, which is different from SubStation proper).

    Subtitles and styles are connected via an :class:`SSAFile` they belong to. :attr:`SSAEvent.style` is a string
    which is (or should be) a key in the :attr:`SSAFile.styles` dict. Note that style name is stored separately;
    a given :class:`SSAStyle` instance has no particular name itself.

    This class defines equality (equality of all fields).

    """
    DEFAULT_STYLE = None

    #: All fields in SSAStyle.
    FIELDS = frozenset([
        "fontname", "fontsize", "primarycolor", "secondarycolor",
        "tertiarycolor", "outlinecolor", "backcolor",
        "bold", "italic", "underline", "strikeout",
        "scalex", "scaley", "spacing", "angle", "borderstyle",
        "outline", "shadow", "alignment",
        "marginl", "marginr", "marginv", "alphalevel", "encoding"
    ])

    def __init__(self, **fields):
        self.fontname = "Arial" #: Font name
        self.fontsize = 20.0 #: Font size (in pixels)
        self.primarycolor = Color(255, 255, 255, 0) #: Primary color (:class:`pysubs2.Color` instance)
        self.secondarycolor = Color(255, 0, 0, 0) #: Secondary color (:class:`pysubs2.Color` instance)
        self.tertiarycolor = Color(0, 0, 0, 0) #: Tertiary color (:class:`pysubs2.Color` instance)
        self.outlinecolor = Color(0, 0, 0, 0) #: Outline color (:class:`pysubs2.Color` instance)
        self.backcolor = Color(0, 0, 0, 0) #: Back, ie. shadow color (:class:`pysubs2.Color` instance)
        self.bold = False #: Bold
        self.italic = False #: Italic
        self.underline = False #: Underline (ASS only)
        self.strikeout = False #: Strikeout (ASS only)
        self.scalex = 100.0 #: Horizontal scaling (ASS only)
        self.scaley = 100.0 #: Vertical scaling (ASS only)
        self.spacing = 0.0 #: Letter spacing (ASS only)
        self.angle = 0.0 #: Rotation (ASS only)
        self.borderstyle = 1 #: Border style
        self.outline = 2.0 #: Outline width (in pixels)
        self.shadow = 2.0 #: Shadow depth (in pixels)
        self.alignment = 2 #: Numpad-style alignment, eg. 7 is "top left" (that is, ASS alignment semantics)
        self.marginl = 10 #: Left margin (in pixels)
        self.marginr = 10 #: Right margin (in pixels)
        self.marginv = 10 #: Vertical margin (in pixels)
        self.alphalevel = 0 #: Old, unused SSA-only field
        self.encoding = 1 #: Charset

        for k, v in fields.items():
            if k in self.FIELDS:
                setattr(self, k, v)
            else:
                raise ValueError("SSAStyle has no field named %r" % k)

    def copy(self):
        return SSAStyle(**self.as_dict())

    def as_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        s = "<SSAStyle "
        s += "%rpx " % self.fontsize
        if self.bold: s += "bold "
        if self.italic: s += "italic "
        s += "'%s'>" % self.fontname
        if not PY3: s = s.encode("utf-8")
        return s


SSAStyle.DEFAULT_STYLE = SSAStyle()
