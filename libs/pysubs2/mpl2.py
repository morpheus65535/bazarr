# coding=utf-8

from __future__ import print_function, division, unicode_literals
import re

from .time import times_to_ms
from .formatbase import FormatBase
from .ssaevent import SSAEvent


# thanks to http://otsaloma.io/gaupol/doc/api/aeidon.files.mpl2_source.html
MPL2_FORMAT = re.compile(r"^(?um)\[(-?\d+)\]\[(-?\d+)\](.*)")


class MPL2Format(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if MPL2_FORMAT.search(text):
            return "mpl2"

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        def prepare_text(lines):
            out = []
            for s in lines.split("|"):
                s = s.strip()

                if s.startswith("/"):
                    # line beginning with '/' is in italics
                    s = r"{\i1}%s{\i0}" % s[1:].strip()

                out.append(s)
            return "\\N".join(out)

        subs.events = [SSAEvent(start=times_to_ms(s=float(start) / 10), end=times_to_ms(s=float(end) / 10),
                       text=prepare_text(text)) for start, end, text in MPL2_FORMAT.findall(fp.getvalue())]

    @classmethod
    def to_file(cls, subs, fp, format_, **kwargs):

        # TODO handle italics
        for line in subs:
            if line.is_comment:
                continue

            print("[{start}][{end}] {text}".format(start=int(line.start // 100),
                                                   end=int(line.end // 100),
                                                   text=line.plaintext.replace("\n", "|")),
                  file=fp)
