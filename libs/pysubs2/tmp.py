from __future__ import print_function, unicode_literals

import re
from .formatbase import FormatBase
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .substation import parse_tags
from .time import ms_to_times, make_time, tmptimestamp_to_ms

#: Pattern that matches TMP timestamp
TMPTIMESTAMP = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})")
#: Pattern that matches TMP line
TMP_LINE = re.compile(r"(\d{1,2}:\d{2}:\d{2}):(.+)")

#: Largest timestamp allowed in Tmp, ie. 99:59:59.
MAX_REPRESENTABLE_TIME = make_time(h=100) - 1

def ms_to_timestamp(ms):
    """Convert ms to 'HH:MM:SS'"""
    # XXX throw on overflow/underflow?
    if ms < 0: ms = 0
    if ms > MAX_REPRESENTABLE_TIME: ms = MAX_REPRESENTABLE_TIME
    h, m, s, ms = ms_to_times(ms)
    return "%02d:%02d:%02d" % (h, m, s)


class TmpFormat(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if "[Script Info]" in text or "[V4+ Styles]" in text:
            # disambiguation vs. SSA/ASS
            return None

        for line in text.splitlines():
            if TMP_LINE.match(line) and len(TMP_LINE.findall(line)) == 1:
                return "tmp"

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        timestamps = [] # (start)
        lines = [] # contains lists of lines following each timestamp

        for line in fp:
            match = TMP_LINE.match(line)
            if not match:
                continue

            start, text = match.groups()
            start = tmptimestamp_to_ms(TMPTIMESTAMP.match(start).groups())
            #calculate endtime from starttime + 500 miliseconds + 67 miliseconds per each character (15 chars per second)
            end = start + 500 + (len(line) * 67)
            timestamps.append((start, end))
            lines.append(text)

        def prepare_text(lines):
            lines = lines.replace("|", r"\N")  # convert newlines
            lines = re.sub(r"< *u *>", "{\\\\u1}", lines) # not r" for Python 2.7 compat, triggers unicodeescape
            lines = re.sub(r"< */? *[a-zA-Z][^>]*>", "", lines) # strip other HTML tags
            return lines

        subs.events = [SSAEvent(start=start, end=end, text=prepare_text(lines))
                       for (start, end), lines in zip(timestamps, lines)]

    @classmethod
    def to_file(cls, subs, fp, format_, **kwargs):
        def prepare_text(text, style):
            body = []
            for fragment, sty in parse_tags(text, style, subs.styles):
                fragment = fragment.replace(r"\h", " ")
                fragment = fragment.replace(r"\n", "\n")
                fragment = fragment.replace(r"\N", "\n")
                if sty.italic: fragment = "<i>%s</i>" % fragment
                if sty.underline: fragment = "<u>%s</u>" % fragment
                if sty.strikeout: fragment = "<s>%s</s>" % fragment
                body.append(fragment)

            return re.sub("\n+", "\n", "".join(body).strip())

        visible_lines = (line for line in subs if not line.is_comment)

        for i, line in enumerate(visible_lines, 1):
            start = ms_to_timestamp(line.start)
            #end = ms_to_timestamp(line.end)
            text = prepare_text(line.text, subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            #print("%d" % i, file=fp) # Python 2.7 compat
            print(start + ":" + text, end="\n", file=fp)
            #print(text, end="\n\n", file=fp)
