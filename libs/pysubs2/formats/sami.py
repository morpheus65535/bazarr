from dataclasses import dataclass
from html.parser import HTMLParser
from typing import List, Optional, TextIO, Any, Tuple

from .base import FormatBase
from ..ssaevent import SSAEvent
from ..ssafile import SSAFile


class SAMIFormat(FormatBase):
    """Synchronized Accessible Media Interchange (SAMI) subtitle format implementation"""

    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if text.lstrip().startswith("<SAMI>"):
            return "sami"

        return None

    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, **kwargs: Any) -> None:
        """
        See :meth:`pysubs2.formats.FormatBase.from_file()`

        Supported tags:

          - ``<i>``
          - ``<u>``
          - ``<s>``
          - ``<b>``
          - ``<br>``

        CSS formatting is not supported.

        """
        parser = SAMIParser()
        parser.feed(fp.read())

        events = []
        for sync_element in parser.sync_elements:
            plaintext = "\n".join(line.strip() for line in sync_element.text.strip().splitlines())
            start_ms = sync_element.start_ms
            # Unfortunately, end timestamp is not given; try to estimate something reasonable:
            # start + 500 ms + 67 ms/character (15 chars per second)
            end_ms = start_ms + 500 + (len(plaintext) * 67)
            event = SSAEvent(
                start=start_ms,
                end=end_ms,
            )
            event.plaintext = plaintext
            events.append(event)

        # correct any overlapping subtitles
        for i in range(len(events) - 1):
            events[i].end = min(events[i].end, events[i + 1].start)

        subs.events.extend(events)


@dataclass
class SyncElement:
    start_ms: int
    text: str


class SAMIParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sync_elements: List[SyncElement] = []
        self.current_sync_element: Optional[SyncElement] = None

    def begin_sync_element(self, start_ms: int) -> None:
        if self.current_sync_element is not None:
            self.close_sync_element()
        self.current_sync_element = SyncElement(start_ms=start_ms, text="")

    def close_sync_element(self) -> None:
        if self.current_sync_element is not None:
            self.sync_elements.append(self.current_sync_element)
            self.current_sync_element = None

    def append_text(self, text: str) -> None:
        if self.current_sync_element is not None:
            self.current_sync_element.text += text

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "sync":
            start_ms = int(dict(attrs)["start"] or 0)
            self.begin_sync_element(start_ms)
        elif tag == "br":
            self.append_text("\n")
        elif tag in ("b", "i", "s", "u"):
            self.append_text("{\\" + tag + "1}")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("sync", "body", "sami"):
            self.close_sync_element()
        elif tag in ("b", "i", "s", "u"):
            self.append_text("{\\" + tag + "0}")

    def handle_data(self, data: str) -> None:
        self.append_text(data)
