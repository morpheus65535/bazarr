import re
from .formatbase import FormatBase
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .substation import parse_tags
from .exceptions import ContentNotUsable
from .time import ms_to_times, make_time, TIMESTAMP, timestamp_to_ms

#: Largest timestamp allowed in SubRip, ie. 99:59:59,999.
MAX_REPRESENTABLE_TIME = make_time(h=100) - 1

def ms_to_timestamp(ms):
    """Convert ms to 'HH:MM:SS,mmm'"""
    # XXX throw on overflow/underflow?
    if ms < 0: ms = 0
    if ms > MAX_REPRESENTABLE_TIME: ms = MAX_REPRESENTABLE_TIME
    h, m, s, ms = ms_to_times(ms)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


class SubripFormat(FormatBase):
    """SubRip Text (SRT) subtitle format implementation"""
    TIMESTAMP = TIMESTAMP

    @staticmethod
    def timestamp_to_ms(groups):
        return timestamp_to_ms(groups)

    @classmethod
    def guess_format(cls, text):
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if "[Script Info]" in text or "[V4+ Styles]" in text:
            # disambiguation vs. SSA/ASS
            return None

        if text.lstrip().startswith("WEBVTT"):
            # disambiguation vs. WebVTT
            return None

        for line in text.splitlines():
            if len(cls.TIMESTAMP.findall(line)) == 2:
                return "srt"

    @classmethod
    def from_file(cls, subs, fp, format_, keep_unknown_html_tags=False, **kwargs):
        """
        See :meth:`pysubs2.formats.FormatBase.from_file()`

        Supported tags:

          - ``<i>``
          - ``<u>``
          - ``<s>``

        Keyword args:
            keep_unknown_html_tags: If True, HTML tags other than i/u/s will be kept as-is.
                Otherwise, they will be stripped from input.
        """
        timestamps = [] # (start, end)
        following_lines = [] # contains lists of lines following each timestamp

        for line in fp:
            stamps = cls.TIMESTAMP.findall(line)
            if len(stamps) == 2: # timestamp line
                start, end = map(cls.timestamp_to_ms, stamps)
                timestamps.append((start, end))
                following_lines.append([])
            else:
                if timestamps:
                    following_lines[-1].append(line)

        def prepare_text(lines):
            # Handle the "happy" empty subtitle case, which is timestamp line followed by blank line(s)
            # followed by number line and timestamp line of the next subtitle. Fixes issue #11.
            if (len(lines) >= 2
                    and all(re.match("\s*$", line) for line in lines[:-1])
                    and re.match("\s*\d+\s*$", lines[-1])):
                return ""

            # Handle the general case.
            s = "".join(lines).strip()
            s = re.sub(r"\n+ *\d+ *$", "", s) # strip number of next subtitle
            s = re.sub(r"< *i *>", r"{\\i1}", s)
            s = re.sub(r"< */ *i *>", r"{\\i0}", s)
            s = re.sub(r"< *s *>", r"{\\s1}", s)
            s = re.sub(r"< */ *s *>", r"{\\s0}", s)
            s = re.sub(r"< *u *>", "{\\\\u1}", s) # not r" for Python 2.7 compat, triggers unicodeescape
            s = re.sub(r"< */ *u *>", "{\\\\u0}", s)
            if not keep_unknown_html_tags:
                s = re.sub(r"< */? *[a-zA-Z][^>]*>", "", s) # strip other HTML tags
            s = re.sub(r"\n", r"\\N", s) # convert newlines
            return s

        subs.events = [SSAEvent(start=start, end=end, text=prepare_text(lines))
                       for (start, end), lines in zip(timestamps, following_lines)]

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
            for fragment, sty in parse_tags(text, style, subs.styles):
                fragment = fragment.replace(r"\h", " ")
                fragment = fragment.replace(r"\n", "\n")
                fragment = fragment.replace(r"\N", "\n")
                if apply_styles:
                    if sty.italic: fragment = "<i>%s</i>" % fragment
                    if sty.underline: fragment = "<u>%s</u>" % fragment
                    if sty.strikeout: fragment = "<s>%s</s>" % fragment
                if sty.drawing: raise ContentNotUsable
                body.append(fragment)

            return re.sub("\n+", "\n", "".join(body).strip())

        visible_lines = (line for line in subs if not line.is_comment)

        lineno = 1
        for line in visible_lines:
            start = ms_to_timestamp(line.start)
            end = ms_to_timestamp(line.end)
            try:
                text = prepare_text(line.text, subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE))
            except ContentNotUsable:
                continue

            print("%d" % lineno, file=fp) # Python 2.7 compat
            print(start, "-->", end, file=fp)
            print(text, end="\n\n", file=fp)
            lineno += 1
