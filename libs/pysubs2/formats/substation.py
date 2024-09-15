import logging
import re
import warnings
from typing import Any, Union, Optional, Dict, Tuple, List, TextIO

from .base import FormatBase
from ..ssaevent import SSAEvent
from ..ssastyle import SSAStyle
from ..common import Color, Alignment, SSA_ALIGNMENT
from ..time import make_time, ms_to_times, timestamp_to_ms, TIMESTAMP, TIMESTAMP_SHORT
from ..ssafile import SSAFile


def ass_to_ssa_alignment(i: int) -> int:
    warnings.warn("ass_to_ssa_alignment function is deprecated, please use the Alignment enum", DeprecationWarning)
    return SSA_ALIGNMENT[i-1]

def ssa_to_ass_alignment(i: int) -> int:
    warnings.warn("ssa_to_ass_alignment function is deprecated, please use the Alignment enum", DeprecationWarning)
    return SSA_ALIGNMENT.index(i) + 1

SECTION_HEADING = re.compile(
    r"^.{,3}"  # allow 3 chars at start of line for BOM
    r"\["  # open square bracket
    r"[^]]*[a-z][^]]*"  # inside square brackets, at least one lowercase letter (this guards vs. uuencoded font data)
    r"]"  # close square bracket
)

ATTACHMENT_FILE_HEADING = re.compile(r"(fontname|filename):\s+(?P<name>\S+)")

STYLE_FORMAT_LINE = {
    "ass": "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic,"
           " Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment,"
           " MarginL, MarginR, MarginV, Encoding",
    "ssa": "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic,"
           " BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding"
}

STYLE_FIELDS = {
    "ass": ["fontname", "fontsize", "primarycolor", "secondarycolor", "outlinecolor", "backcolor", "bold", "italic",
            "underline", "strikeout", "scalex", "scaley", "spacing", "angle", "borderstyle", "outline", "shadow",
            "alignment", "marginl", "marginr", "marginv", "encoding"],
    "ssa": ["fontname", "fontsize", "primarycolor", "secondarycolor", "tertiarycolor", "backcolor", "bold", "italic",
            "borderstyle", "outline", "shadow", "alignment", "marginl", "marginr", "marginv", "alphalevel", "encoding"]
}

EVENT_FORMAT_LINE = {
    "ass": "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    "ssa": "Format: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
}

EVENT_FIELDS = {
    "ass": ["layer", "start", "end", "style", "name", "marginl", "marginr", "marginv", "effect", "text"],
    "ssa": ["marked", "start", "end", "style", "name", "marginl", "marginr", "marginv", "effect", "text"]
}

#: Largest timestamp allowed in SubStation, ie. 9:59:59.99.
MAX_REPRESENTABLE_TIME = make_time(h=10) - 10

def color_to_ass_rgba(c: Color) -> str:
    return f"&H{((c.a << 24) | (c.b << 16) | (c.g << 8) | c.r):08X}"

def color_to_ssa_rgb(c: Color) -> str:
    return f"{((c.b << 16) | (c.g << 8) | c.r)}"

def rgba_to_color(s: str) -> Color:
    if s[0] == '&':
        x = int(s[2:], base=16)
    else:
        x = int(s)
    r = x & 0xff
    g = (x >> 8) & 0xff
    b = (x >> 16) & 0xff
    a = (x >> 24) & 0xff
    return Color(r, g, b, a)

def is_valid_field_content(s: str) -> bool:
    """
    Returns True if string s can be stored in a SubStation field.

    Fields are written in CSV-like manner, thus commas and/or newlines
    are not acceptable in the string.

    """
    return "\n" not in s and "," not in s


def parse_tags(text: str, style: SSAStyle = SSAStyle.DEFAULT_STYLE,
               styles: Optional[Dict[str, SSAStyle]] = None) -> List[Tuple[str, SSAStyle]]:
    """
    Split text into fragments with computed SSAStyles.
    
    Returns list of tuples (fragment, style), where fragment is a part of text
    between two brace-delimited override sequences, and style is the computed
    styling of the fragment, ie. the original style modified by all override
    sequences before the fragment.
    
    Newline and non-breakable space overrides are left as-is.
    
    Supported override tags:
    
    - i, b, u, s
    - r (with or without style name)
    
    """
    if styles is None:
        styles = {}
    
    fragments = SSAEvent.OVERRIDE_SEQUENCE.split(text)
    if len(fragments) == 1:
        return [(text, style)]
    
    def apply_overrides(all_overrides: str) -> SSAStyle:
        s = style.copy()
        for tag in re.findall(r"\\[ibusp][0-9]|\\r[a-zA-Z_0-9 ]*", all_overrides):
            if tag == r"\r":
                s = style.copy() # reset to original line style
            elif tag.startswith(r"\r"):
                name = tag[2:]
                if name in styles:
                    # reset to named style
                    s = styles[name].copy()
            else:
                if "i" in tag:
                    s.italic = "1" in tag
                elif "b" in tag:
                    s.bold = "1" in tag
                elif "u" in tag:
                    s.underline = "1" in tag
                elif "s" in tag:
                    s.strikeout = "1" in tag
                elif "p" in tag:
                    try:
                        scale = int(tag[2:])
                    except (ValueError, IndexError):
                        continue

                    s.drawing = scale > 0
        return s
    
    overrides = SSAEvent.OVERRIDE_SEQUENCE.findall(text)
    overrides_prefix_sum = ["".join(overrides[:i]) for i in range(len(overrides) + 1)]
    computed_styles = map(apply_overrides, overrides_prefix_sum)
    return list(zip(fragments, computed_styles))


NOTICE = "Script generated by pysubs2\nhttps://pypi.python.org/pypi/pysubs2"

class SubstationFormat(FormatBase):
    """SubStation Alpha (ASS, SSA) subtitle format implementation"""

    @staticmethod
    def ms_to_timestamp(requested_ms: int) -> str:
        """Convert ms to 'H:MM:SS.cc'"""
        if requested_ms < 0:
            requested_ms = 0
        if requested_ms > MAX_REPRESENTABLE_TIME:
            warnings.warn("Overflow in SubStation timestamp, clamping to MAX_REPRESENTABLE_TIME", RuntimeWarning)
            requested_ms = MAX_REPRESENTABLE_TIME

        # Aegisub does rounding, see https://github.com/Aegisub/Aegisub/blob/6f546951b4f004da16ce19ba638bf3eedefb9f31/libaegisub/include/libaegisub/ass/time.h#L32
        round_ms = ((requested_ms + 5) - (requested_ms + 5) % 10)
        h, m, s, ms = ms_to_times(round_ms)
        cs = ms // 10

        return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if re.search(r"V4\+ Styles", text, re.IGNORECASE):
            return "ass"
        elif re.search(r"V4 Styles", text, re.IGNORECASE):
            return "ssa"
        else:
            return None

    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """See :meth:`pysubs2.formats.FormatBase.from_file()`"""

        def string_to_field(f: str, v: str) -> Any:
            # Per issue #45, we should handle the case where there is extra whitespace around the values.
            # Extra whitespace is removed in non-string fields where it would break the parser otherwise,
            # and in font name (where it doesn't really make sense). It is preserved in Dialogue string
            # fields like Text, Name and Effect (to avoid introducing unnecessary change to parser output).

            if f in {"start", "end"}:
                v = v.strip()
                if v.startswith("-"):
                    # handle negative timestamps
                    v = v[1:]
                    sign = -1
                else:
                    sign = 1

                m = TIMESTAMP.match(v)
                if m is None:
                    m = TIMESTAMP_SHORT.match(v)
                    if m is None:
                        raise ValueError(f"Failed to parse timestamp: {v!r}")

                return sign * timestamp_to_ms(m.groups())
            elif "color" in f:
                v = v.strip()
                return rgba_to_color(v)
            elif f in {"bold", "underline", "italic", "strikeout"}:
                return v != "0"
            elif f in {"borderstyle", "encoding", "marginl", "marginr", "marginv", "layer", "alphalevel"}:
                try:
                    return int(v)
                except ValueError:
                    warnings.warn(f"Failed to parse {f}, using default", RuntimeWarning)
                    return 0
            elif f in {"fontsize", "scalex", "scaley", "spacing", "angle", "outline", "shadow"}:
                return float(v)
            elif f == "marked":
                return v.endswith("1")
            elif f == "alignment":
                try:
                    if format_ == "ass":
                        return Alignment(int(v))
                    else:
                        return Alignment.from_ssa_alignment(int(v))
                except Exception:
                    warnings.warn("Failed to parse alignment, using default", RuntimeWarning)
                    return Alignment.BOTTOM_CENTER
            elif f == "fontname":
                return v.strip()
            else:
                return v

        subs.info.clear()
        subs.aegisub_project.clear()
        subs.styles.clear()
        subs.fonts_opaque.clear()
        subs.graphics_opaque.clear()

        inside_info_section = False
        inside_aegisub_section = False
        inside_font_section = False
        inside_graphic_section = False
        current_attachment_name = None
        current_attachment_lines_buffer = []
        current_attachment_is_font = None

        for lineno, line in enumerate(fp, 1):
            line = line.strip()

            if SECTION_HEADING.match(line):
                logging.debug("at line %d: section heading %s", lineno, line)
                inside_info_section = "Info" in line
                inside_aegisub_section = "Aegisub" in line
                inside_font_section = "Fonts" in line
                inside_graphic_section = "Graphics" in line
            elif inside_info_section or inside_aegisub_section:
                if line.startswith(";"):
                    continue  # skip comments
                try:
                    k, v = line.split(":", 1)
                    if inside_info_section:
                        subs.info[k] = v.strip()
                    elif inside_aegisub_section:
                        subs.aegisub_project[k] = v.strip()
                except ValueError:
                    pass
            elif inside_font_section or inside_graphic_section:
                m = ATTACHMENT_FILE_HEADING.match(line)
                current_attachment_is_font = inside_font_section

                if current_attachment_name and (m or not line):
                    # flush last font/picture on newline or new font/picture name
                    attachment_data = current_attachment_lines_buffer[:]
                    if inside_font_section:
                        subs.fonts_opaque[current_attachment_name] = attachment_data
                    elif inside_graphic_section:
                        subs.graphics_opaque[current_attachment_name] = attachment_data
                    else:
                        raise NotImplementedError("Bad attachment section, expected [Fonts] or [Graphics]")
                    logging.debug("at line %d: finished attachment definition %s", lineno, current_attachment_name)
                    current_attachment_lines_buffer.clear()
                    current_attachment_name = None

                if m:
                    # start new font/picture
                    attachment_name = m.group("name")
                    current_attachment_name = attachment_name
                elif line:
                    # add non-empty line to current buffer
                    current_attachment_lines_buffer.append(line)
            elif line.startswith("Style:"):
                _, rest = line.split(":", 1)
                buf = rest.strip().split(",")
                name, *raw_fields = buf
                field_dict = {f: string_to_field(f, v) for f, v in zip(STYLE_FIELDS[format_], raw_fields)}
                sty = SSAStyle(**field_dict)
                subs.styles[name] = sty
            elif line.startswith("Dialogue:") or line.startswith("Comment:"):
                ev_type, rest = line.split(":", 1)
                raw_fields = rest.strip().split(",", len(EVENT_FIELDS[format_])-1)
                field_dict = {f: string_to_field(f, v) for f, v in zip(EVENT_FIELDS[format_], raw_fields)}
                field_dict["type"] = ev_type
                ev = SSAEvent(**field_dict)
                subs.events.append(ev)

        # cleanup fonts/pictures
        if current_attachment_name:
            # flush last font on EOF or new section w/o newline
            attachment_data = current_attachment_lines_buffer[:]

            if current_attachment_is_font:
                subs.fonts_opaque[current_attachment_name] = attachment_data
            else:
                subs.graphics_opaque[current_attachment_name] = attachment_data

            logging.debug("at EOF: finished attachment definition %s", current_attachment_name)
            current_attachment_lines_buffer.clear()
            current_attachment_name = None

    @classmethod
    def to_file(cls, subs: "SSAFile", fp: TextIO, format_: str, header_notice: str = NOTICE, **kwargs: Any) -> None:
        """See :meth:`pysubs2.formats.FormatBase.to_file()`"""
        print("[Script Info]", file=fp)
        for line in header_notice.splitlines(False):
            print(";", line, file=fp)

        subs.info["ScriptType"] = "v4.00+" if format_ == "ass" else "v4.00"
        for k, v in subs.info.items():
            print(k, v, sep=": ", file=fp)

        if subs.aegisub_project:
            print("\n[Aegisub Project Garbage]", file=fp)
            for k, v in subs.aegisub_project.items():
                print(k, v, sep=": ", file=fp)

        def field_to_string(f: str, v: Any, line: Union[SSAEvent, SSAStyle]) -> str:
            if f in {"start", "end"}:
                return cls.ms_to_timestamp(v)
            elif f == "marked":
                return f"Marked={v:d}"
            elif f == "alignment":
                if isinstance(v, Alignment):
                    alignment = v
                else:
                    warnings.warn("The 'alignment' attribute of SSAStyle should be an Alignment instance, using plain int is deprecated", DeprecationWarning)
                    alignment = Alignment(v)

                if format_ == "ssa":
                    return str(alignment.to_ssa_alignment())
                else:
                    return str(alignment.value)
            elif isinstance(v, bool):
                return "-1" if v else "0"
            elif isinstance(v, int):
                return str(v)
            elif isinstance(v, float):
                return str(int(v) if v.is_integer() else v)
            elif isinstance(v, str):
                return v
            elif isinstance(v, Color):
                if format_ == "ass":
                    return color_to_ass_rgba(v)
                else:
                    return color_to_ssa_rgb(v)
            else:
                raise TypeError(f"Unexpected type when writing a SubStation field {f!r} for line {line!r}")

        print("\n[V4+ Styles]" if format_ == "ass" else "\n[V4 Styles]", file=fp)
        print(STYLE_FORMAT_LINE[format_], file=fp)
        for name, sty in subs.styles.items():
            fields = [field_to_string(f, getattr(sty, f), sty) for f in STYLE_FIELDS[format_]]
            print(f"Style: {name}", *fields, sep=",", file=fp)

        if subs.fonts_opaque:
            print("\n[Fonts]", file=fp)
            for font_name, font_lines in sorted(subs.fonts_opaque.items()):
                print(f"fontname: {font_name}", file=fp)
                for line in font_lines:
                    print(line, file=fp)
                print(file=fp)

        if subs.graphics_opaque:
            print("\n[Graphics]", file=fp)
            for picture_name, picture_lines in sorted(subs.graphics_opaque.items()):
                print(f"filename: {picture_name}", file=fp)
                for line in picture_lines:
                    print(line, file=fp)
                print(file=fp)

        print("\n[Events]", file=fp)
        print(EVENT_FORMAT_LINE[format_], file=fp)
        for ev in subs.events:
            fields = [field_to_string(f, getattr(ev, f), ev) for f in EVENT_FIELDS[format_]]
            print(ev.type, end=": ", file=fp)
            print(*fields, sep=",", file=fp)
