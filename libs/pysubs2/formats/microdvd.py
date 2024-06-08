from functools import partial
import re
from typing import Optional, TextIO, Any, Match

from ..exceptions import UnknownFPSError
from ..ssaevent import SSAEvent
from ..ssastyle import SSAStyle
from .base import FormatBase
from .substation import parse_tags
from ..time import ms_to_frames, frames_to_ms
from ..ssafile import SSAFile


#: Matches a MicroDVD line.
MICRODVD_LINE = re.compile(r" *\{ *(\d+) *\} *\{ *(\d+) *\}(.+)")


class MicroDVDFormat(FormatBase):
    """MicroDVD subtitle format implementation"""
    @classmethod
    def guess_format(cls, text: str) -> Optional[str]:
        """See :meth:`pysubs2.formats.FormatBase.guess_format()`"""
        if any(map(MICRODVD_LINE.match, text.splitlines())):
            return "microdvd"
        else:
            return None

    @classmethod
    def from_file(cls, subs: "SSAFile", fp: TextIO, format_: str, fps: Optional[float] = None,
                  strict_fps_inference: bool = True, **kwargs: Any) -> None:
        """
        See :meth:`pysubs2.formats.FormatBase.from_file()`

        Keyword args:
            strict_fps_inference: If True (default), in the case when ``fps`` is not given, it will be read
                from the first subtitle text only if the start and end frame of this subtitle is ``{1}{1}``
                (matches VLC Player behaviour), otherwise :class:`pysubs2.exceptions.UnknownFPSError` is raised.

                When ``strict_fps_inference``
                is False, framerate will be read from the first subtitle text in this case regardless of
                start and end frame (which may result in bogus result, if the first subtitle is not supposed
                to contain framerate). Before introduction of this option, the library behaved as if this
                option was False.

                .. versionchanged:: 1.7.0
                   Added the ``strict_fps_inference`` option.
        """
        for line in fp:
            match = MICRODVD_LINE.match(line)
            if not match:
                continue

            fstart, fend, text = match.groups()
            fstart, fend = map(int, (fstart, fend))

            if fps is None:
                # We don't know the framerate, but it is customary to include it as text of the first subtitle,
                # in the format {1}{1}fps, see pysubs2 issue #71 or VLC player source:
                # https://code.videolan.org/videolan/vlc/-/blob/dccda0e133ff0a2e85de727cf19ddbc634f06b67/modules/demux/subtitle.c#L1014
                # In that case, we skip this auxiliary subtitle and proceed with reading.
                try:
                    if strict_fps_inference and not (fstart == 1 and fend == 1):
                        raise ValueError("Frame mismatch, expected {1}{1}")

                    fps = float(text)
                    subs.fps = fps
                    continue
                except ValueError:
                    raise UnknownFPSError("Framerate was not specified and "
                                          "cannot be read from "
                                          "the MicroDVD file.")

            start, end = map(partial(frames_to_ms, fps=fps), (fstart, fend))

            def prepare_text(text: str) -> str:
                text = text.replace("|", r"\N")

                def style_replacer(match: Match[str]) -> str:
                    tags = [c for c in "biu" if c in match.group(0)]
                    return "{%s}" % "".join(f"\\{c}1" for c in tags)

                text = re.sub(r"\{[Yy]:[^}]+\}", style_replacer, text)
                text = re.sub(r"\{[Ff]:([^}]+)\}", r"{\\fn\1}", text)
                text = re.sub(r"\{[Ss]:([^}]+)\}", r"{\\fs\1}", text)
                text = re.sub(r"\{P:(\d+),(\d+)\}", r"{\\pos(\1,\2)}", text)

                return text.strip()

            ev = SSAEvent(start=start, end=end, text=prepare_text(text))
            subs.append(ev)

    @classmethod
    def to_file(cls, subs: "SSAFile", fp: TextIO, format_: str, fps: Optional[float] = None,
                write_fps_declaration: bool = True, apply_styles: bool = True, **kwargs: Any) -> None:
        """
        See :meth:`pysubs2.formats.FormatBase.to_file()`

        The only supported styling is marking whole lines italic.

        Keyword args:
            write_fps_declaration: If True, create a zero-duration first subtitle ``{1}{1}`` which will contain
                the fps.
            apply_styles: If False, do not write any styling.

        """
        if fps is None:
            fps = subs.fps

        if fps is None:
            raise UnknownFPSError("Framerate must be specified when writing MicroDVD.")
        to_frames = partial(ms_to_frames, fps=fps)

        def is_entirely_italic(line: SSAEvent) -> bool:
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
            subs.insert(0, SSAEvent(start=1, end=1, text=str(fps)))

        for line in subs.get_text_events():
            text = "|".join(line.plaintext.splitlines())
            if apply_styles and is_entirely_italic(line):
                text = "{Y:i}" + text

            start, end = map(to_frames, (line.start, line.end))

            # XXX warn on underflow?
            if start < 0:
                start = 0
            if end < 0:
                end = 0

            print("{%d}{%d}%s" % (start, end, text), file=fp)

        # remove the artificial framerate-telling line
        if write_fps_declaration:
            subs.pop(0)
