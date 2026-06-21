import warnings
from typing import Any, ClassVar
import dataclasses

from .common import Color, Alignment


@dataclasses.dataclass(repr=False)
class SSAStyle:
    """
    A SubStation Style.

    In SubStation, each subtitle (:class:`SSAEvent`) is associated with a style which defines its font, color, etc.
    Like a subtitle event, a style also consists of "fields"; see :attr:`SSAStyle.FIELDS` for a list
    (note the spelling, which is different from SubStation proper).

    Subtitles and styles are connected via an :class:`SSAFile` they belong to. :attr:`SSAEvent.style` is a string
    which is (or should be) a key in the :attr:`SSAFile.styles` dict. Note that style name is stored separately;
    a given :class:`SSAStyle` instance has no particular name itself.

    This class defines equality (equality of all fields).

    Attributes:
        fontname: Font name
        fontsize: Font size (in pixels)
        primarycolor: Primary color (:class:`pysubs2.Color` instance)
        secondarycolor: Secondary color (:class:`pysubs2.Color` instance)
        tertiarycolor: Tertiary color (:class:`pysubs2.Color` instance)
        outlinecolor: Outline color (:class:`pysubs2.Color` instance)
        backcolor: Back, ie. shadow color (:class:`pysubs2.Color` instance)
        bold: Bold
        italic: Italic
        underline: Underline (ASS only)
        strikeout: Strikeout (ASS only)
        scalex: Horizontal scaling (ASS only)
        scaley: Vertical scaling (ASS only)
        spacing: Letter spacing (ASS only)
        angle: Rotation (ASS only)
        borderstyle: Border style (1=outline, 3=box)
        outline: Outline width (in pixels)
        shadow: Shadow depth (in pixels)
        alignment: Text alignment (:class:`pysubs2.Alignment` instance); the underlying integer
            uses numpad-style alignment, eg. 7 is "top left" (that is, ASS alignment semantics).
            You can also use ``int`` here, though it is discouraged.
        marginl: Left margin (in pixels)
        marginr: Right margin (in pixels)
        marginv: Vertical margin (in pixels)
        alphalevel: Old, unused SSA-only field
        encoding: Charset
        drawing: Indicates that text span is a SSA vector drawing, see :func:`pysubs2.substation.parse_tags()`

    """
    DEFAULT_STYLE: ClassVar["SSAStyle"] = None  # type: ignore[assignment]

    @property
    def FIELDS(self) -> frozenset[str]:
        """All fields in SSAStyle."""
        warnings.warn("Deprecated in 1.2.0 - it's a dataclass now", DeprecationWarning)
        return frozenset(field.name for field in dataclasses.fields(self))

    fontname: str = "Arial"
    fontsize: float = 20.0
    primarycolor: Color = dataclasses.field(default_factory=lambda: Color(255, 255, 255, 0))
    secondarycolor: Color = dataclasses.field(default_factory=lambda: Color(255, 0, 0, 0))
    tertiarycolor: Color = dataclasses.field(default_factory=lambda: Color(0, 0, 0, 0))
    outlinecolor: Color = dataclasses.field(default_factory=lambda: Color(0, 0, 0, 0))
    backcolor: Color = dataclasses.field(default_factory=lambda: Color(0, 0, 0, 0))
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikeout: bool = False
    scalex: float = 100.0
    scaley: float = 100.0
    spacing: float = 0.0
    angle: float = 0.0
    borderstyle: int = 1
    outline: float = 2.0
    shadow: float = 2.0
    alignment: Alignment = Alignment.BOTTOM_CENTER
    marginl: int = 10
    marginr: int = 10
    marginv: int = 10
    alphalevel: int = 0
    encoding: int = 1

    # The following attributes cannot be defined for SSA styles themselves,
    # but can be used in override tags and thus are useful to keep here
    # for the `pysubs2.substation.parse_tags()` interface which returns
    # SSAStyles for text fragments.
    drawing: bool = False

    def copy(self) -> "SSAStyle":
        return SSAStyle(**self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        # dataclasses.asdict() would recursively dictify Color objects, which we don't want
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}

    def __repr__(self) -> str:
        return f"<SSAStyle {self.fontsize!r}px" \
               f"{' bold' if self.bold else ''}" \
               f"{' italic' if self.italic else ''}" \
               f" {self.fontname!r}>"


SSAStyle.DEFAULT_STYLE = SSAStyle()
