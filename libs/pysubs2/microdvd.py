from __future__ import unicode_literals, print_function

from functools import partial
import re
from .common import text_type
from .exceptions import UnknownFPSError
from .ssaevent import SSAEvent
from .ssastyle import SSAStyle
from .formatbase import FormatBase
from .substation import parse_tags
from .time import ms_to_frames, frames_to_ms

#: Matches a MicroDVD line.
MICRODVD_LINE = re.compile(r" *\{ *(\d+) *\} *\{ *(\d+) *\}(.+)")


class MicroDVDFormat(FormatBase):
    @classmethod
    def guess_format(cls, text):
        if any(map(MICRODVD_LINE.match, text.splitlines())):
            return "microdvd"

    @classmethod
    def from_file(cls, subs, fp, format_, fps=None, **kwargs):
        for line in fp:
            match = MICRODVD_LINE.match(line)
            if not match:
                continue

            fstart, fend, text = match.groups()
            fstart, fend = map(int, (fstart, fend))

            if fps is None:
                # We don't know the framerate, but it is customary to include
                # it as text of the first subtitle. In that case, we skip
                # this auxiliary subtitle and proceed with reading.
                try:
                    fps = float(text)
                    subs.fps = fps
                    continue
                except ValueError:
                    raise UnknownFPSError("Framerate was not specified and "
                                          "cannot be read from "
                                          "the MicroDVD file.")

            start, end = map(partial(frames_to_ms, fps=fps), (fstart, fend))

            def prepare_text(text):
                text = text.replace("|", r"\N")

                def style_replacer(match):
                    tags = [c for c in "biu" if c in match.group(0)]
                    return "{%s}" % "".join(r"\%s1" % c for c in tags)

                text = re.sub(r"\{[Yy]:[^}]+\}", style_replacer, text)
                text = re.sub(r"\{[Ff]:([^}]+)\}", r"{\\fn\1}", text)
                text = re.sub(r"\{[Ss]:([^}]+)\}", r"{\\fs\1}", text)
                text = re.sub(r"\{P:(\d+),(\d+)\}", r"{\\pos(\1,\2)}", text)

                return text.strip()

            ev = SSAEvent(start=start, end=end, text=prepare_text(text))
            subs.append(ev)

    @classmethod
    def to_file(cls, subs, fp, format_, fps=None, write_fps_declaration=True, **kwargs):
        if fps is None:
            fps = subs.fps

        if fps is None:
            raise UnknownFPSError("Framerate must be specified when writing MicroDVD.")
        to_frames = partial(ms_to_frames, fps=fps)

        def is_entirely_italic(line):
            style = subs.styles.get(line.style, SSAStyle.DEFAULT_STYLE)
            for fragment, sty in parse_tags(line.text, style, subs.styles):
                fragment = fragment.replace(r"\h", " ")
                fragment = fragment.replace(r"\n", "\n")
                fragment = fragment.replace(r"\N", "\n")
                if not sty.italic and fragment and not fragment.isspace():
                    return False
            return True

        # insert an artificial first line telling the framerate
        if write_fps_declaration:
            subs.insert(0, SSAEvent(start=0, end=0, text=text_type(fps)))

        for line in (ev for ev in subs if not ev.is_comment):
            text = "|".join(line.plaintext.splitlines())
            if is_entirely_italic(line):
                text = "{Y:i}" + text

            start, end = map(to_frames, (line.start, line.end))

            # XXX warn on underflow?
            if start < 0: start = 0
            if end < 0: end = 0

            print("{%d}{%d}%s" % (start, end, text), file=fp)

        # remove the artificial framerate-telling line
        if write_fps_declaration:
            subs.pop(0)
