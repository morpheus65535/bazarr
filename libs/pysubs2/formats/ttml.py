import re
from enum import Enum
from typing import Optional, TextIO, Any, Dict, List, Union
import xml.etree.ElementTree as ET

from .base import FormatBase
from ..common import etree_iter_child_nodes, etree_register_namespace_override, etree_append_child_nodes
from ..ssaevent import SSAEvent
from ..ssastyle import SSAStyle
from .substation import parse_tags
from ..time import ms_to_times, make_time
from ..ssafile import SSAFile


TT_NS = "{http://www.w3.org/ns/ttml}"
TTS_NS = "{http://www.w3.org/ns/ttml#styling}"


class TimeContainer(Enum):
    PAR = "par"
    SEQ = "seq"


class TTMLFormat(FormatBase):
    """Timed Text Markup Language (TTML) subtitle format implementation"""

    @staticmethod
    def ms_to_timestamp(ms: int) -> str:
        """Convert ms to 'HH:MM:SS.mmm'"""
        if ms < 0:
            ms = 0
        h, m, s, ms = ms_to_times(ms)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    @staticmethod
    def timestamp_to_ms(expr: str) -> int:
        # offset-time (not supported: f, t)
        m = re.fullmatch(r"(\d+(?:\.\d+)?)(h|m|s|ms)", expr)
        if m is not None:
            count = int(m.group(1)) if m.group(1).isnumeric() else float(m.group(1))
            metric = m.group(2)
            return make_time(**{metric: count})  # type: ignore[arg-type]

        # clock-time (not supported: frames, subframes)
        m = re.fullmatch(r"(\d{2,}):(\d{2}):(\d{2}(?:\.\d+)?)", expr)
        if m is not None:
            hours = int(m.group(1))
            minutes = int(m.group(2))
            seconds = int(m.group(3)) if m.group(3).isnumeric() else float(m.group(3))
            return make_time(h=hours, m=minutes, s=seconds)

        raise NotImplementedError(f"Unsupported time expression: {expr}")

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if "http://www.w3.org/ns/ttml" in text:
            return "ttml"

        return None

    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        Rudimentary TTML parser. No formatting/styling apart from newlines is supported.
        Frame-based time expressions are not supported.

        """
        tree = ET.parse(fp)
        root = tree.getroot()

        body_elem = root.find(f"{TT_NS}body")
        if body_elem is None:
            return

        cls._parse_body(subs, body_elem)

    @classmethod
    def _parse_body(cls, subs: "SSAFile", body_elem: ET.Element) -> None:
        begin_ms = cls.timestamp_to_ms(body_elem.attrib.get("begin", "0s"))
        time_container = TimeContainer(body_elem.attrib.get("timeContainer", "par"))
        if time_container != TimeContainer.PAR:
            raise NotImplementedError("Only 'par' timeContainer is supported")

        for div_elem in body_elem.iterfind(f"{TT_NS}div"):
            cls._parse_div(subs, div_elem, begin_ms)

    @classmethod
    def _parse_div(cls, subs: "SSAFile", div_elem: ET.Element, parent_begin_ms: int) -> None:
        begin_ms = cls.timestamp_to_ms(div_elem.attrib.get("begin", "0s")) + parent_begin_ms
        time_container = TimeContainer(div_elem.attrib.get("timeContainer", "par"))
        if time_container != TimeContainer.PAR:
            raise NotImplementedError("Only 'par' timeContainer is supported")

        for p_elem in div_elem.iterfind(f"{TT_NS}p"):
            cls._parse_p(subs, p_elem, begin_ms)

    @classmethod
    def _parse_p(cls, subs: "SSAFile", p_elem: ET.Element, parent_begin_ms: int) -> None:
        begin_ms = cls.timestamp_to_ms(p_elem.attrib.get("begin", "0s")) + parent_begin_ms
        if "duration" in p_elem.attrib:
            end_ms = begin_ms + cls.timestamp_to_ms(p_elem.attrib["duration"])
        else:
            end_ms = cls.timestamp_to_ms(p_elem.attrib["end"]) + parent_begin_ms
        time_container = TimeContainer(p_elem.attrib.get("timeContainer", "par"))
        if time_container != TimeContainer.PAR:
            raise NotImplementedError("Only 'par' timeContainer is supported")

        event = SSAEvent(start=begin_ms, end=end_ms)
        subs.events.append(event)

        for node in etree_iter_child_nodes(p_elem):
            if isinstance(node, str):
                event.text += node.strip().replace("\n", " ")
            else:
                if node.tag == f"{TT_NS}br":
                    event.text += "\\N"
                elif node.tag == f"{TT_NS}span":
                    cls._parse_span(event, node)

    @classmethod
    def _parse_span(cls, event: SSAEvent, span_elem: ET.Element) -> None:
        for node in etree_iter_child_nodes(span_elem):
            if isinstance(node, str):
                event.text += node.strip().replace("\n", " ")
            else:
                if node.tag == f"{TT_NS}br":
                    event.text += "\\N"
                elif node.tag == f"{TT_NS}span":
                    cls._parse_span(event, node)

    @classmethod
    def to_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        TTML writer. Has partial support for styles and override tags.

        Supported styling:
            - bold
            - italic
            - font name
            - primary color
            - underline
            - strikeout
        """

        tt_elem = ET.Element(f"{TT_NS}tt")
        head_elem = ET.SubElement(tt_elem, f"{TT_NS}head")
        body_elem = ET.SubElement(tt_elem, f"{TT_NS}body")
        div_elem = ET.SubElement(body_elem, f"{TT_NS}div")
        styling_elem = ET.SubElement(head_elem, f"{TT_NS}styling")

        for name, style in subs.styles.items():
            attrs = {
                "id": name,
                **cls.ssastyle_to_tts(style),
            }
            ET.SubElement(styling_elem, f"{TT_NS}style", attrs)

        for event in subs.get_text_events():
            event_style = subs.styles.get(event.style, SSAStyle.DEFAULT_STYLE)
            attrs = {
                "begin": str(cls.ms_to_timestamp(event.start)),
                "end": str(cls.ms_to_timestamp(event.end)),
                "style": event.style,
            }
            p_elem = ET.SubElement(div_elem, f"{TT_NS}p", attrs)

            runs = parse_tags(event.text, event_style, subs.styles, skip_empty_fragments=True)

            if len(runs) == 1:
                fragment, sty = runs[0]
                p_elem.attrib.update(cls.ssastyle_to_tts(sty, event_style))
                cls._append_text(p_elem, fragment)
            else:
                for fragment, sty in runs:
                    attrs = cls.ssastyle_to_tts(sty, event_style)
                    if attrs:
                        span_elem = ET.SubElement(p_elem, f"{TT_NS}span", attrs)
                        cls._append_text(span_elem, fragment)
                    else:
                        cls._append_text(p_elem, fragment)

        with etree_register_namespace_override():
            ET.register_namespace("", "http://www.w3.org/ns/ttml")
            ET.register_namespace("ttm", "http://www.w3.org/ns/ttml#metadata")
            ET.register_namespace("tts", "http://www.w3.org/ns/ttml#styling")
            ET.indent(tt_elem)
            output_xml = ET.tostring(tt_elem).decode("utf-8")
            print(output_xml, file=fp)

    @classmethod
    def ssastyle_to_tts(cls, style: SSAStyle, base_style: Optional[SSAStyle] = None) -> Dict[str, str]:
        """
        Convert `SSAStyle` (or its difference to base style) into dictionary of XML attributes

        Reference: https://www.w3.org/TR/ttml1/#styling-attribute-vocabulary
        """
        attrs = {}

        decorations = []
        if style.underline and (base_style is None or base_style.underline != style.underline):
            decorations.append("underline")
        elif not style.underline and base_style is not None and base_style.underline:
            decorations.append("noUnderline")
        if style.strikeout and (base_style is None or base_style.strikeout != style.strikeout):
            decorations.append("lineThrough")
        elif not style.strikeout and base_style is not None and base_style.strikeout:
            decorations.append("noLineThrough")

        if decorations:
            attrs[f"{TTS_NS}textDecoration"] = " ".join(decorations)

        if base_style is None or (style.fontname != base_style.fontname):
            attrs[f"{TTS_NS}fontFamily"] = style.fontname
        if base_style is None or base_style.bold != style.bold:
            attrs[f"{TTS_NS}fontWeight"] = "bold" if style.bold else "normal"
        if base_style is None or base_style.italic != style.italic:
            attrs[f"{TTS_NS}fontStyle"] = "italic" if style.italic else "normal"
        if base_style is None or base_style.primarycolor != style.primarycolor:
            attrs[f"{TTS_NS}color"] = "#{0.r:02X}{0.g:02X}{0.b:02X}".format(style.primarycolor)

        return attrs

    @classmethod
    def _append_text(cls, elem: ET.Element, text: str) -> None:
        text = text.replace("\\h", " ")
        chunks = re.split(r"\\[Nn]", text)
        nodes: List[Union[ET.Element, str]] = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                nodes.append(ET.Element(f"{TT_NS}br"))
            nodes.append(chunk)

        etree_append_child_nodes(elem, nodes)
