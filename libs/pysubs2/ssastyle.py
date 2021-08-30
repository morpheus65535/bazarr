import warnings
from typing import Dict, Any, ClassVar
import dataclasses

from .common import Color

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

    """
    DEFAULT_STYLE: ClassVar["SSAStyle"] = None

    @property
    def FIELDS(self):
        """All fields in SSAStyle."""
        warnings.warn("Deprecated in 1.2.0 - it's a dataclass now", DeprecationWarning)
        return frozenset(field.name for field in dataclasses.fields(self))

    fontname: str = "Arial"  #: Font name
    fontsize: float = 20.0  #: Font size (in pixels)
    primarycolor: Color = Color(255, 255, 255, 0)  #: Primary color (:class:`pysubs2.Color` instance)
    secondarycolor: Color = Color(255, 0, 0, 0)  #: Secondary color (:class:`pysubs2.Color` instance)
    tertiarycolor: Color = Color(0, 0, 0, 0)  #: Tertiary color (:class:`pysubs2.Color` instance)
    outlinecolor: Color = Color(0, 0, 0, 0)  #: Outline color (:class:`pysubs2.Color` instance)
    backcolor: Color = Color(0, 0, 0, 0)  #: Back, ie. shadow color (:class:`pysubs2.Color` instance)
    bold: bool = False  #: Bold
    italic: bool = False  #: Italic
    underline: bool = False  #: Underline (ASS only)
    strikeout: bool = False  #: Strikeout (ASS only)
    scalex: float = 100.0  #: Horizontal scaling (ASS only)
    scaley: float = 100.0  #: Vertical scaling (ASS only)
    spacing: float = 0.0  #: Letter spacing (ASS only)
    angle: float = 0.0  #: Rotation (ASS only)
    borderstyle: int = 1  #: Border style
    outline: float = 2.0  #: Outline width (in pixels)
    shadow: float = 2.0  #: Shadow depth (in pixels)
    alignment: int = 2  #: Numpad-style alignment, eg. 7 is "top left" (that is, ASS alignment semantics)
    marginl: int = 10  #: Left margin (in pixels)
    marginr: int = 10  #: Right margin (in pixels)
    marginv: int = 10  #: Vertical margin (in pixels)
    alphalevel: int = 0  #: Old, unused SSA-only field
    encoding: int = 1  #: Charset

    # The following attributes cannot be defined for SSA styles themselves,
    # but can be used in override tags and thus are useful to keep here
    # for the `pysubs2.substation.parse_tags()` interface which returns
    # SSAStyles for text fragments.
    drawing: bool = False  #: Indicates that text span is a SSA vector drawing, see `pysubs2.substation.parse_tags()`

    def copy(self) -> "SSAStyle":
        return SSAStyle(**self.as_dict())

    def as_dict(self) -> Dict[str, Any]:
        # dataclasses.asdict() would recursively dictify Color objects, which we don't want
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}

    def __repr__(self):
        return f"<SSAStyle {self.fontsize!r}px" \
               f"{' bold' if self.bold else ''}" \
               f"{' italic' if self.italic else ''}" \
               f" {self.fontname!r}>"


SSAStyle.DEFAULT_STYLE = SSAStyle()
