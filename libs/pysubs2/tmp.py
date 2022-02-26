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


class TmpFormat(FormatBase):
    """TMP subtitle format implementation"""

    @staticmethod
    def ms_to_timestamp(ms: int) -> str:
        """Convert ms to 'HH:MM:SS'"""
        # XXX throw on overflow/underflow?
        if ms < 0: ms = 0
        if ms > MAX_REPRESENTABLE_TIME: ms = MAX_REPRESENTABLE_TIME
        h, m, s, ms = ms_to_times(ms)
        return "%02d:%02d:%02d" % (h, m, s)

    @classmethod
    def guess_format(cls, text):
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if "[Script Info]" in text or "[V4+ Styles]" in text:
            # disambiguation vs. SSA/ASS
            return None

        for line in text.splitlines():
            if TMP_LINE.match(line) and len(TMP_LINE.findall(line)) == 1:
                return "tmp"

    @classmethod
    def from_file(cls, subs, fp, format_, **kwargs):
        """See :meth:`pysubs2.formats.FormatBase.from_file()`"""
        events = []

        def prepare_text(text):
            text = text.replace("|", r"\N")  # convert newlines
            text = re.sub(r"< *u *>", "{\\\\u1}", text) # not r" for Python 2.7 compat, triggers unicodeescape
            text = re.sub(r"< */? *[a-zA-Z][^>]*>", "", text) # strip other HTML tags
            return text

        for line in fp:
            match = TMP_LINE.match(line)
            if not match:
                continue

            start, text = match.groups()
            start = tmptimestamp_to_ms(TMPTIMESTAMP.match(start).groups())

            # Unfortunately, end timestamp is not given; try to estimate something reasonable:
            # start + 500 ms + 67 ms/character (15 chars per second)
            end_guess = start + 500 + (len(line) * 67)

            event = SSAEvent(start=start, end=end_guess, text=prepare_text(text))
            events.append(event)

        # correct any overlapping subtitles created by end_guess
        for i in range(len(events) - 1):
            events[i].end = min(events[i].end, events[i+1].start)

        subs.events = events

    @classmethod
    def to_file(cls, subs, fp, format_, apply_styles=True, **kwargs):
        """
        See :meth:`pysubs2.formats.FormatBase.to_file()`

        Italic, underline and strikeout styling is supported.

        Keyword args:
            apply_styles: If False, do not write any styling.

        """
        def prepare_text(text, style):
            body = []
            skip = False
            for fragment, sty in parse_tags(text, style, subs.styles):
                fragment = fragment.replace(r"\h", " ")
                fragment = fragment.replace(r"\n", "\n")
                fragment = fragment.replace(r"\N", "\n")
                if apply_styles:
                    if sty.italic: fragment = "<i>%s</i>" % fragment
                    if sty.underline: fragment = "<u>%s</u>" % fragment
                    if sty.strikeout: fragment = "<s>%s</s>" % fragment
                if sty.drawing: skip = True
                body.append(fragment)

            if skip:
                return ""
            else:
                return re.sub("\n+", "\n", "".join(body).strip())

        visible_lines = (line for line in subs if not line.is_comment)

        for line in visible_lines:
            start = cls.ms_to_timestamp(line.start)
            text = prepare_text(line.text, subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE))

            print(start + ":" + text, end="\n", file=fp)
