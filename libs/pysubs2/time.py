import re
from typing import Optional, Sequence, NamedTuple

from .common import IntOrFloat

#: Pattern that matches both SubStation and SubRip timestamps.
TIMESTAMP = re.compile(r"(\d{1,2}):(\d{1,2}):(\d{1,2})[.,](\d{1,3})")

#: Pattern that matches H:MM:SS or HH:MM:SS timestamps.
TIMESTAMP_SHORT = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})")


class Times(NamedTuple):
    """Named tuple (h, m, s, ms) of ints."""
    h: int
    m: int
    s: int
    ms: int


def make_time(h: IntOrFloat = 0, m: IntOrFloat = 0, s: IntOrFloat = 0, ms: IntOrFloat = 0,
              frames: Optional[int] = None, fps: Optional[float] = None) -> int:
    """
    Convert time to milliseconds.

    See :func:`pysubs2.time.times_to_ms()`. When both frames and fps are specified,
    :func:`pysubs2.time.frames_to_ms()` is called instead.

    Raises:
        ValueError: Invalid fps, or one of frames/fps is missing.

    Example:
        >>> make_time(s=1.5)
        1500
        >>> make_time(frames=50, fps=25)
        2000

    """
    if frames is None and fps is None:
        return times_to_ms(h, m, s, ms)
    elif frames is not None and fps is not None:
        return frames_to_ms(frames, fps)
    else:
        raise ValueError("Both fps and frames must be specified")


def timestamp_to_ms(groups: Sequence[str]) -> int:
    """
    Convert groups from :data:`pysubs2.time.TIMESTAMP` or :data:`pysubs2.time.TIMESTAMP_SHORT`
    match to milliseconds.
    
    Example:
        >>> timestamp_to_ms(TIMESTAMP.match("0:00:00.42").groups())
        420
        >>> timestamp_to_ms(TIMESTAMP_SHORT.match("0:00:01").groups())
        1000

    """
    h: int
    m: int
    s: int
    ms: int
    frac: int
    if len(groups) == 4:
        h, m, s, frac = map(int, groups)
        ms = frac * 10**(3 - len(groups[-1]))
    elif len(groups) == 3:
        h, m, s = map(int, groups)
        ms = 0
    else:
        raise ValueError("Unexpected number of groups")

    ms += s * 1000
    ms += m * 60000
    ms += h * 3600000
    return ms


def times_to_ms(h: IntOrFloat = 0, m: IntOrFloat = 0, s: IntOrFloat = 0, ms: IntOrFloat = 0) -> int:
    """
    Convert hours, minutes, seconds to milliseconds.
    
    Arguments may be positive or negative, int or float,
    need not be normalized (``s=120`` is okay).
    
    Returns:
        Number of milliseconds (rounded to int).
    
    """
    ms += s * 1000
    ms += m * 60000
    ms += h * 3600000
    return int(round(ms))


def frames_to_ms(frames: int, fps: float) -> int:
    """
    Convert frame-based duration to milliseconds.
    
    Arguments:
        frames: Number of frames (should be int).
        fps: Framerate (must be a positive number, eg. 23.976).
    
    Returns:
        Number of milliseconds (rounded to int).
        
    Raises:
        ValueError: fps was negative or zero.
    
    """
    if fps <= 0:
        raise ValueError(f"Framerate must be a positive number ({fps}).")

    return int(round(frames * (1000 / fps)))


def ms_to_frames(ms: IntOrFloat, fps: float) -> int:
    """
    Convert milliseconds to number of frames.
    
    Arguments:
        ms: Number of milliseconds (may be int, float or other numeric class).
        fps: Framerate (must be a positive number, eg. 23.976).
    
    Returns:
        Number of frames (int).
        
    Raises:
        ValueError: fps was negative or zero.
    
    """
    if fps <= 0:
        raise ValueError(f"Framerate must be a positive number ({fps}).")

    return int(round((ms / 1000) * fps))


def ms_to_times(ms: IntOrFloat) -> Times:
    """
    Convert milliseconds to normalized tuple (h, m, s, ms).
    
    Arguments:
        ms: Number of milliseconds (may be int, float or other numeric class).
            Should be non-negative.
    
    Returns:
        Named tuple (h, m, s, ms) of ints.
        Invariants: ``ms in range(1000) and s in range(60) and m in range(60)``
    
    """
    ms = int(round(ms))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return Times(h, m, s, ms)


def ms_to_str(ms: IntOrFloat, fractions: bool = False) -> str:
    """
    Prettyprint milliseconds to [-]H:MM:SS[.mmm]
    
    Handles huge and/or negative times. Non-negative times with ``fractions=True``
    are matched by :data:`pysubs2.time.TIMESTAMP`.
    
    Arguments:
        ms: Number of milliseconds (int, float or other numeric class).
        fractions: Whether to print up to millisecond precision.
    
    Returns:
        str
    
    """
    sgn = "-" if ms < 0 else ""
    h, m, s, ms = ms_to_times(abs(ms))
    if fractions:
        return f"{sgn}{h:01d}:{m:02d}:{s:02d}.{ms:03d}"
    else:
        return f"{sgn}{h:01d}:{m:02d}:{s:02d}"
