# coding=utf-8

from __future__ import print_function, division, unicode_literals
import re
from numbers import Number

from pysubs2.time import times_to_ms
from .formatbase import FormatBase
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle


# thanks to http://otsaloma.io/gaupol/doc/api/aeidon.files.mpl2_source.html
MPL2_FORMAT = re.compile(r"^(?um)\[(-?\d+)\]\[(-?\d+)\](.*?)$")


class TXTGenericFormat(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if MPL2_FORMAT.match(text):
            return "mpl2"


class MPL2Format(FormatBase):
    @classmethod
    def guess_format(cls, text):
        return TXTGenericFormat.guess_format(text)

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        def prepare_text(lines):
            out = []
            for s in lines.split("|"):
                if s.startswith("/"):
                    out.append(r"{\i1}%s{\i0}" % s[1:])
                    continue
                out.append(s)
            return "\n".join(out)

        subs.events = [SSAEvent(start=times_to_ms(s=float(start) / 10), end=times_to_ms(s=float(end) / 10),
                       text=prepare_text(text)) for start, end, text in MPL2_FORMAT.findall(fp.getvalue())]

    @classmethod
    def to_file(cls, subs, fp, format_, **kwargs):
        raise NotImplemented
