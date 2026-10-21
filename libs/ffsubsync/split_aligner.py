# -*- coding: utf-8 -*-
"""alass-style split-penalty alignment.

ffsubsync's default aligner (:class:`ffsubsync.aligners.FFTAligner`) emits a single
global offset for the whole file. That cannot correct a subtitle whose required
offset *changes* partway through -- e.g. a commercial break, an inserted/removed
scene ("director's cut"), or two discs concatenated into one file.

This module implements the core idea from `alass <https://github.com/kaegi/alass>`_:
let every cue take its own offset, but charge a *split penalty* every time two
consecutive cues are assigned different offsets. We maximize::

    sum_i rating(cue_i @ offset_i)  -  split_penalty * (number of splits)

via dynamic programming, yielding a piecewise-constant offset function. With a large
penalty the optimum collapses to a single global offset (i.e. the default behavior).

Rating
------
The base rating of a cue ``[start, end]`` placed at offset ``o`` against the reference
speech signal is the overlap length, which -- given the prefix sum of the reference --
is an O(1) lookup::

    rating(cue, o) = ref_cumsum[end + o] - ref_cumsum[start + o]

Two refinements over the plain overlap (both faithful to alass, both still O(1)):

* **Length / edge penalty ("standard scoring").** Pure overlap is flat wherever a cue
  sits entirely inside a longer reference-speech block, so it cannot localize a short
  cue within a long block, nor prefer a same-length block over a longer one. We
  additionally subtract a fraction of the reference speech in a guard band just
  *outside* the cue's edges, which rewards the cue's edges lining up with the speech
  boundaries (a same-sized block wins over a longer one). This needs two extra
  prefix-sum lookups per cue.

* **Sub-sample (piecewise-linear) offsets.** The reference is a 0/1 step function, so
  its prefix sum is exactly recovered at fractional positions by *linear interpolation*
  (``cumsum[k] + ref[k]*frac``). Evaluating the rating on an offset grid finer than one
  sample therefore yields the exact continuous overlap, giving sub-``1/sample_rate``
  offset precision. Controlled by ``offset_step_samples`` (< 1 => finer than one sample).

The whole DP is ``O(n_cues * n_offsets)`` and fully numpy-vectorizable, with no
dependency beyond numpy.
"""
import logging
from typing import List, Tuple, Union

import numpy as np

from ffsubsync.generic_subtitles import GenericSubtitle
from ffsubsync.speech_transformers import _is_metadata

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


# Upper bound (in samples) on the length-penalty guard band. The guard is normally
# the cue's own duration (a scale-free "is this block about my size?" probe), but a
# very long cue would otherwise reach across neighbouring dialogue and penalize a
# perfectly good placement, so we clamp it here (2s at 100Hz).
_MAX_GUARD_SAMPLES: int = 200


def _cue_sample_bounds(
    cues: List[GenericSubtitle], sample_rate: int, start_seconds: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return per-cue ``(start_sample, end_sample, is_speech)`` arrays.

    Bounds are kept as floats (no rounding to whole samples) so the sub-sample
    offset grid can exploit their true millisecond timing. The ``_is_metadata`` gate
    matches :class:`SubtitleSpeechTransformer` so non-dialogue cues (blank lines,
    bracketed sound cues, music notes, ...) are marked non-speech and contribute no
    rating -- the DP then leaves them on a neighbour's offset for free.
    """
    n = len(cues)
    starts = np.zeros(n, dtype=np.float64)
    ends = np.zeros(n, dtype=np.float64)
    is_speech = np.zeros(n, dtype=bool)
    for i, sub in enumerate(cues):
        start = (sub.start.total_seconds() - start_seconds) * sample_rate
        duration = (sub.end.total_seconds() - sub.start.total_seconds()) * sample_rate
        starts[i] = start
        ends[i] = start + duration
        is_speech[i] = not _is_metadata(sub.content, i == 0 or i + 1 == n)
    return starts, ends, is_speech


def compute_split_offsets(
    reference: np.ndarray,
    cues: List[GenericSubtitle],
    *,
    sample_rate: int,
    start_seconds: float,
    split_penalty: float,
    max_offset_samples: int,
    length_penalty: float = 0.0,
    offset_step_samples: float = 1.0,
    return_score: bool = False,
    log_segments: bool = True,
) -> Union[List[float], Tuple[List[float], float]]:
    """Return one offset (in samples) per cue, aligned 1:1 with ``cues``.

    Parameters
    ----------
    reference:
        The reference speech signal (1.0 where speech is present), as produced by a
        reference pipeline at ``sample_rate`` Hz.
    cues:
        The (already framerate-scaled) subtitle cues to align.
    split_penalty:
        Cost, in *overlap samples*, charged each time consecutive cues take different
        offsets. Larger => fewer splits; very large => a single global offset.
    max_offset_samples:
        Half-width of the candidate offset grid; offsets range over
        ``[-max_offset_samples, +max_offset_samples]``.
    length_penalty:
        Weight of the edge/length term ("standard scoring"). 0 => pure overlap.
    offset_step_samples:
        Spacing of the candidate offset grid, in samples. 1.0 => whole samples
        (default); values < 1 give sub-sample precision via linear interpolation.
    return_score:
        If True, also return the maximized objective value (used to compare
        alignments across candidate framerate scales).
    log_segments:
        If True, log a human-readable summary of the resulting segments.
    """
    n = len(cues)
    if n == 0:
        return ([], 0.0) if return_score else []

    starts, ends, is_speech = _cue_sample_bounds(cues, sample_rate, start_seconds)
    guards = np.minimum(ends - starts, float(_MAX_GUARD_SAMPLES))

    step = float(offset_step_samples)
    if step <= 0:
        step = 1.0
    n_off = int(round(2 * max_offset_samples / step)) + 1
    offsets = -float(max_offset_samples) + step * np.arange(n_off)

    # Prefix sum of the (binary) reference so overlap is an O(1) difference. Pad both
    # ends -- by the offset half-width plus the max guard band -- so every shifted /
    # guard-extended lookup lands inside a flat region (0 on the left, total speech on
    # the right) that correctly contributes no extra speech. `pos + pad` maps a
    # reference position `pos` into `padded`.
    ref = (np.asarray(reference, dtype=np.float64) > 0).astype(np.float64)
    cumsum = np.concatenate([np.zeros(1), np.cumsum(ref)])  # cumsum[k] = sum(ref[:k])
    pad = max_offset_samples + _MAX_GUARD_SAMPLES + 2
    padded = np.concatenate([np.zeros(pad), cumsum, np.full(pad, cumsum[-1])])
    max_pos = len(padded) - 1

    def _interp(pos: np.ndarray) -> np.ndarray:
        # Linear interpolation of the prefix sum. Because `ref` is a 0/1 step function,
        # cumsum[k] + ref[k]*frac is the *exact* integral up to a fractional position,
        # so this is the exact overlap for fractional offsets (not an approximation).
        pos = np.clip(pos, 0.0, float(max_pos))
        lo = np.floor(pos).astype(np.int64)
        np.clip(lo, 0, max_pos - 1, out=lo)
        frac = pos - lo
        return padded[lo] * (1.0 - frac) + padded[lo + 1] * frac

    def _rating_row(i: int) -> np.ndarray:
        if not is_speech[i]:
            return np.zeros(n_off)
        start_pos = starts[i] + offsets + pad
        end_pos = ends[i] + offsets + pad
        cs = _interp(start_pos)
        ce = _interp(end_pos)
        overlap = ce - cs
        if length_penalty and guards[i] > 0:
            gl = cs - _interp(start_pos - guards[i])  # speech just before the cue
            gr = _interp(end_pos + guards[i]) - ce  # speech just after the cue
            return overlap - length_penalty * (gl + gr)
        return overlap

    # Forward DP. dp[o] = best total rating for cues[0..i] with cue i at offset o.
    # back[i, o] records whether cue i kept the previous cue's offset (-1) or jumped,
    # in which case the previous cue sat at the argmax of the previous row.
    dp = _rating_row(0)
    back = np.full((n, n_off), -1, dtype=np.int64)  # row 0 unused (no predecessor)
    for i in range(1, n):
        best_prev_idx = int(np.argmax(dp))
        jump_value = dp[best_prev_idx] - split_penalty
        keep_value = dp  # same offset, no penalty
        jumped = jump_value > keep_value
        dp = _rating_row(i) + np.where(jumped, jump_value, keep_value)
        back[i] = np.where(jumped, best_prev_idx, -1)

    best_total = float(dp.max())

    # Backtrack.
    offset_idx = np.empty(n, dtype=np.int64)
    cur = int(np.argmax(dp))
    for i in range(n - 1, -1, -1):
        offset_idx[i] = cur
        if i > 0:
            b = int(back[i, cur])
            cur = b if b >= 0 else cur

    result = [float(offsets[idx]) for idx in offset_idx]
    if log_segments:
        log_split_segments(result, sample_rate)
    if return_score:
        return result, best_total
    return result


def log_split_segments(offsets: List[float], sample_rate: int) -> None:
    """Emit a human-readable summary of the piecewise offset function."""
    if not offsets:
        return
    segments: List[Tuple[int, float]] = []  # (count, offset_samples)
    for off in offsets:
        if segments and segments[-1][1] == off:
            segments[-1] = (segments[-1][0] + 1, off)
        else:
            segments.append((1, off))
    n_splits = len(segments) - 1
    logger.info("split alignment: %d segment(s), %d split(s)", len(segments), n_splits)
    for count, off in segments:
        logger.info("  %d cue(s) offset %.3fs", count, off / float(sample_rate))
