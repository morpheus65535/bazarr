import re
from .formatbase import FormatBase
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .substation import parse_tags
from .exceptions import ContentNotUsable
from .time import ms_to_times, make_time, TIMESTAMP, timestamp_to_ms

#: Largest timestamp allowed in SubRip, ie. 99:59:59,999.
MAX_REPRESENTABLE_TIME = make_time(h=100) - 1


class SubripFormat(FormatBase):
    """SubRip Text (SRT) subtitle format implementation"""
    TIMESTAMP = TIMESTAMP

    @staticmethod
    def ms_to_timestamp(ms: int) -> str:
        """Convert ms to 'HH:MM:SS,mmm'"""
        # XXX throw on overflow/underflow?
        if ms < 0: ms = 0
        if ms > MAX_REPRESENTABLE_TIME: ms = MAX_REPRESENTABLE_TIME
        h, m, s, ms = ms_to_times(ms)
        return "%02d:%02d:%02d,%03d" % (h, m, s, ms)

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
    def from_file(cls, subs, fp, format_, keep_html_tags=False, keep_unknown_html_tags=False, **kwargs):
        """
        See :meth:`pysubs2.formats.FormatBase.from_file()`

        Supported tags:

          - ``<i>``
          - ``<u>``
          - ``<s>``
          - ``<b>``

        Keyword args:
            keep_html_tags: If True, all HTML tags will be kept as-is instead of being
                converted to SubStation tags (eg. you will get ``<i>example</i>`` instead of ``{\\i1}example{\\i0}``).
                Setting this to True overrides the ``keep_unknown_html_tags`` option.
            keep_unknown_html_tags: If True, supported HTML tags will be converted
                to SubStation tags and any other HTML tags will be kept as-is
                (eg. you would get ``<blink>example {\\i1}text{\\i0}</blink>``).
                If False, these other HTML tags will be stripped from output
                (in the previous example, you would get only ``example {\\i1}text{\\i0}``).
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
                    and all(re.match(r"\s*$", line) for line in lines[:-1])
                    and re.match(r"\s*\d+\s*$", lines[-1])):
                return ""

            # Handle the general case.
            s = "".join(lines).strip()
            s = re.sub(r"\n+ *\d+ *$", "", s) # strip number of next subtitle
            if not keep_html_tags:
                s = re.sub(r"< *i *>", r"{\\i1}", s)
                s = re.sub(r"< */ *i *>", r"{\\i0}", s)
                s = re.sub(r"< *s *>", r"{\\s1}", s)
                s = re.sub(r"< */ *s *>", r"{\\s0}", s)
                s = re.sub(r"< *u *>", r"{\\u1}", s)
                s = re.sub(r"< */ *u *>", r"{\\u0}", s)
                s = re.sub(r"< *b *>", r"{\\b1}", s)
                s = re.sub(r"< */ *b *>", r"{\\b0}", s)
            if not (keep_html_tags or keep_unknown_html_tags):
                s = re.sub(r"< */? *[a-zA-Z][^>]*>", "", s) # strip other HTML tags
            s = re.sub(r"\n", r"\\N", s) # convert newlines
            return s

        subs.events = [SSAEvent(start=start, end=end, text=prepare_text(lines))
                       for (start, end), lines in zip(timestamps, following_lines)]

    @classmethod
    def to_file(cls, subs, fp, format_, apply_styles=True, keep_ssa_tags=False, **kwargs):
        """
        See :meth:`pysubs2.formats.FormatBase.to_file()`

        Italic, underline and strikeout styling is supported.

        Keyword args:
            apply_styles: If False, do not write any styling (ignore line style
                and override tags).
            keep_ssa_tags: If True, instead of trying to convert inline override
                tags to HTML (as supported by SRT), any inline tags will be passed
                to output (eg. ``{\\an7}``, which would be otherwise stripped;
                or ``{\\b1}`` instead of ``<b>``). Whitespace tags ``\\h``, ``\\n``
                and ``\\N`` will always be converted to whitespace regardless of
                this option. In the current implementation, enabling this option
                disables processing of line styles - you will get inline tags but
                if for example line's style is italic you will not get ``{\\i1}``
                at the beginning of the line. (Since this option is mostly useful
                for dealing with non-standard SRT files, ie. both input and output
                is SRT which doesn't use line styles - this shouldn't be much
                of an issue in practice.)
        """
        def prepare_text(text: str, style: SSAStyle):
            text = text.replace(r"\h", " ")
            text = text.replace(r"\n", "\n")
            text = text.replace(r"\N", "\n")

            body = []
            if keep_ssa_tags:
                body.append(text)
            else:
                for fragment, sty in parse_tags(text, style, subs.styles):
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
            start = cls.ms_to_timestamp(line.start)
            end = cls.ms_to_timestamp(line.end)
            try:
                text = prepare_text(line.text, subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE))
            except ContentNotUsable:
                continue

            print("%d" % lineno, file=fp) # Python 2.7 compat
            print(start, "-->", end, file=fp)
            print(text, end="\n\n", file=fp)
            lineno += 1
