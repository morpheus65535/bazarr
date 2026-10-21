"""This is a python implementation of clip()."""
from __future__ import annotations

# std imports
import os
import sys
import enum
from itertools import islice

from typing import Literal, Callable, Optional, NamedTuple

# local
from ._width import width
from .grapheme import iter_graphemes
from .hyperlink import Hyperlink, HyperlinkParams
from .sgr_state import (_SGR_PATTERN,
                        _SGR_STATE_DEFAULT,
                        _SGRState,
                        _sgr_state_update,
                        _sgr_state_is_active,
                        _sgr_state_to_sequence)
from ._constants import _clamp_ambiguous_width
from .text_sizing import TextSizing, TextSizingParams
from .escape_sequences import (_SEQUENCE_CLASSIFY,
                               _HORIZONTAL_CURSOR_MOVEMENT,
                               INDETERMINATE_EFFECT_SEQUENCE)

_c_clip: Optional[Callable[..., Optional[str]]]  # pylint: disable=invalid-name
if os.environ.get('WCWIDTH_PYTHON', ''):
    _c_clip = None
else:
    try:
        # local
        from ._wcwidth_c import clip as _c_clip_impl
    except ImportError:
        _c_clip = None
    else:
        _c_clip = _c_clip_impl


class _HyperlinkAction(enum.Enum):
    """Outcome of processing an OSC 8 hyperlink unit."""

    NO_CLOSE = enum.auto()   # open sequence without matching close
    EMPTY = enum.auto()       # hyperlink with no visible inner text
    OUTSIDE = enum.auto()     # hyperlink entirely outside the clip window
    VISIBLE = enum.auto()     # hyperlink overlaps the clip window


class _HyperlinkResult(NamedTuple):
    """
    Result of processing an OSC 8 hyperlink.

    Only the fields relevant to each action are populated.
    """

    action: _HyperlinkAction
    close_end: int = 0
    inner_width: int = 0
    open_seq: str = ''
    clipped_inner: str = ''
    close_seq: str = ''
    clipped_width: int = 0
    hl_col_end: int = 0


def _apply_sgr_wrap(result: str, captured_style: Optional[_SGRState],
                    end_style: Optional[_SGRState] = None) -> str:
    """
    Apply SGR prefix/suffix around *result*.

    If an SGR state was captured at the first visible character, prefix the result with the
    corresponding SGR sequence, and suffix with a reset if any styles remain active at the end
    of the clipped region.

    *end_style* is the style in effect after the final SGR sequence emitted within the clip window,
    or ``None`` when no such sequence was emitted, the style at the first visible character is still
    in effect.  This matches :func:`wcwidth.propagate_sgr`, which decides the trailing reset by SGR
    state at the end of each line.
    """
    if captured_style is not None:
        if prefix := _sgr_state_to_sequence(captured_style):
            result = prefix + result
        if _sgr_state_is_active(captured_style if end_style is None else end_style):
            result += '\x1b[0m'
    return result


def _process_hyperlink(
    text: str,
    start: int,
    end: int,
    fillchar: str,
    tabsize: int,
    ambiguous_width: int,
    term_program: bool | str,
    control_codes: Literal['parse', 'strict', 'ignore'],
    *,
    params: HyperlinkParams,
    match_end: int,
    col: int,
) -> _HyperlinkResult:
    """
    Process an OSC 8 hyperlink unit.

    Finds the matching close sequence, measures the inner text width, and determines whether the
    hyperlink is empty, outside the clip window, or visible (requiring inner-text clipping).
    """
    # pylint: disable=too-many-locals,too-many-positional-arguments,too-many-arguments
    close_start, close_end = Hyperlink.find_close(text, match_end)
    if (close_start, close_end) == (-1, -1):
        return _HyperlinkResult(_HyperlinkAction.NO_CLOSE)
    inner_text = text[match_end:close_start]
    inner_width = width(
        inner_text, control_codes=control_codes,
        tabsize=tabsize, ambiguous_width=ambiguous_width,
        term_program=term_program,
    )

    if inner_width == 0:
        return _HyperlinkResult(_HyperlinkAction.EMPTY, close_end=close_end)

    hl_col_end = col + inner_width

    if hl_col_end <= start or col >= end:
        return _HyperlinkResult(_HyperlinkAction.OUTSIDE, close_end=close_end,
                                inner_width=inner_width)

    inner_clip_start = max(0, start - col)
    inner_clip_end = end - col

    clipped_inner = clip(
        inner_text, inner_clip_start, inner_clip_end,
        fillchar=fillchar, tabsize=tabsize,
        ambiguous_width=ambiguous_width,
        term_program=term_program,
        propagate_sgr=False,
        control_codes=control_codes,
    )

    clipped_width = width(
        clipped_inner, control_codes=control_codes,
        tabsize=tabsize, ambiguous_width=ambiguous_width,
        term_program=term_program,
    )

    return _HyperlinkResult(
        _HyperlinkAction.VISIBLE,
        close_end=close_end,
        inner_width=inner_width,
        open_seq=params.make_open(),
        clipped_inner=clipped_inner,
        close_seq=params.make_close(),
        clipped_width=clipped_width,
        hl_col_end=hl_col_end,
    )


def _reconstruct_painter(
    cells: dict[int, tuple[str, int]],
    sequences: list[tuple[int, int, str]],
    start: int,
    end: int,
    fillchar: str,
) -> str:
    """
    Reconstruct the output string from painter's algorithm state.

    Walks columns left-to-right, interleaving escape sequences and cell content, filling gaps with
    *fillchar*.
    """
    # pylint: disable=too-many-locals
    # Group and sort sequences by column, preserving insertion order within each.
    seqs_by_col: dict[int, list[tuple[int, str]]] = {}
    for col_pos, order, seq_text in sequences:
        seqs_by_col.setdefault(col_pos, []).append((order, seq_text))
    for entries in seqs_by_col.values():
        entries.sort()

    max_cell_col = max(cells.keys()) if cells else -1
    max_seq_col = max(seqs_by_col.keys()) if seqs_by_col else -1
    max_col = max(max_cell_col, max_seq_col)

    parts: list[str] = []
    walk_col = 0
    col_limit = min(max_col, end)
    while walk_col <= col_limit:
        # Emit any sequences anchored at this column.
        for _, seq_text in seqs_by_col.get(walk_col, ()):
            parts.append(seq_text)

        if walk_col >= end:
            walk_col += 1
            continue

        if walk_col in cells:
            cell_text, cell_w = cells[walk_col]
            parts.append(cell_text)
            walk_col += cell_w or 1
        else:
            if start <= walk_col <= max_cell_col:
                parts.append(fillchar)
            walk_col += 1

    # Emit sequences anchored beyond the visible region.
    for c in sorted(seqs_by_col.keys()):
        if c > col_limit:
            for _, seq_text in seqs_by_col[c]:
                parts.append(seq_text)

    return ''.join(parts)


def _clip_simple(
    text: str,
    start: int,
    end: int,
    *,
    propagate_sgr: bool,
    ambiguous_width: int,
    term_program: bool | str,
    fillchar: str,
    tabsize: int,
    control_codes: Literal['parse', 'strict', 'ignore'],
) -> tuple[str, Optional[_SGRState], Optional[_SGRState]]:
    """
    Clip text without cursor movement (simple append-to-output path).

    Returns ``(result, captured_style, end_style)``.  The caller applies SGR wrapping.
    """
    # pylint: disable=too-complex,too-many-locals,too-many-branches,too-many-statements
    # pylint: disable=too-many-nested-blocks
    # code length and complexity traded for performance, to allow this to be used as a "hot path"

    strict = control_codes == 'strict'

    output: list[str] = []
    col = 0
    idx = 0
    captured_style: Optional[_SGRState] = None
    end_style: Optional[_SGRState] = None
    current_style = _SGR_STATE_DEFAULT if propagate_sgr else None

    while idx < len(text):
        char = text[idx]

        # Early exit: past visible region.
        if col >= end and char not in '\r\x08\t\x1b':
            if captured_style is not None:
                break
            # propagate_sgr is always False here: with propagate_sgr=True,
            # captured_style is set on the first visible emission in the
            # clip window and we would have broken above.  The skip-ahead
            # optimization is only needed (and safe) when SGR tracking is off.
            next_esc = text.find('\x1b', idx + 1)
            if next_esc == -1:
                break
            idx = next_esc
            continue

        if char == '\x1b':
            m = _SEQUENCE_CLASSIFY.match(text, idx)
            if not m:
                output.append(char)
                idx += 1
                continue

            # SGR: update current_style.  Sequences before the first visible
            # emission are folded into the prefix synthesized by
            # _apply_sgr_wrap(); those inside the clip window are emitted at
            # their original position; those at or beyond *end* are dropped.
            if m.group('sgr_params') is not None and propagate_sgr and current_style is not None:
                current_style = _sgr_state_update(current_style, m.group())
                if captured_style is not None and col < end:
                    output.append(m.group())
                    end_style = current_style
                idx = m.end()
                continue

            # OSC 8 hyperlink.
            if hl_state := HyperlinkParams.parse(m.group()):
                r = _process_hyperlink(
                    text, start, end, fillchar, tabsize, ambiguous_width,
                    term_program,
                    control_codes,
                    params=hl_state, match_end=m.end(), col=col,
                )
                if r.action is _HyperlinkAction.NO_CLOSE:
                    output.append(m.group())
                    idx = m.end()
                elif r.action is _HyperlinkAction.EMPTY:
                    idx = r.close_end
                elif r.action is _HyperlinkAction.OUTSIDE:
                    col += r.inner_width
                    idx = r.close_end
                else:
                    output.append(r.open_seq)
                    output.append(r.clipped_inner)
                    output.append(r.close_seq)
                    if propagate_sgr and captured_style is None:
                        captured_style = current_style
                    # Inner text is clipped with propagate_sgr=False, so any SGR
                    # sequences it emits are verbatim: fold them into our state.
                    if propagate_sgr and current_style is not None:
                        for sgr_m in _SGR_PATTERN.finditer(r.clipped_inner):
                            current_style = _sgr_state_update(current_style, sgr_m.group())
                            end_style = current_style
                    col += r.inner_width
                    idx = r.close_end
                continue

            # OSC 66 Text Sizing.
            if (ts_meta := m.group('ts_meta')) is not None:
                ts_text = m.group('ts_text') or ''
                ts_term = m.group('ts_term')
                assert ts_term is not None
                ts = TextSizing(
                    TextSizingParams.from_params(ts_meta, control_codes=control_codes),
                    ts_text, ts_term)
                ts_width = ts.display_width(ambiguous_width)

                if col >= start and col + ts_width <= end:
                    output.append(ts.make_sequence())
                    if propagate_sgr and captured_style is None:
                        captured_style = current_style
                    col += ts_width
                elif col < end and col + ts_width > start:
                    ts_parts: list[str] = []

                    def _ts_write(s: str, _w: int, _col: int) -> None:
                        ts_parts.append(s)
                    col = _text_sizing_clip(
                        ts, col, start, end, fillchar, ambiguous_width,
                        term_program,
                        _ts_write)
                    output.extend(ts_parts)
                    if propagate_sgr and captured_style is None:
                        captured_style = current_style
                else:
                    col += ts_width
                idx = m.end()
                continue

            # Indeterminate-effect sequences: raise in strict mode.
            seq = m.group()
            if strict and INDETERMINATE_EFFECT_SEQUENCE.match(seq):
                raise ValueError(
                    f"Indeterminate cursor sequence at position {idx}, "
                    f"{seq!r}"
                )

            # Any other recognized sequence: preserve as-is.
            output.append(seq)
            idx = m.end()
            continue

        if char == '\t':
            # Expand tab, filling clip window with spaces.
            if tabsize > 0:
                next_tab = col + (tabsize - (col % tabsize))
                while col < next_tab:
                    if start <= col < end:
                        output.append(' ')
                        if propagate_sgr and captured_style is None:
                            captured_style = current_style
                    col += 1
            elif start <= col < end:
                output.append('\t')
            idx += 1
            continue

        grapheme = next(iter_graphemes(text, start=idx))
        grapheme_w = width(grapheme, ambiguous_width=ambiguous_width,
                           term_program=term_program)

        # Emit grapheme or fillchar depending on visibility within clip window.
        if grapheme_w == 0:
            if start <= col < end:
                output.append(grapheme)
        elif col >= start and col + grapheme_w <= end:
            output.append(grapheme)
            if propagate_sgr and captured_style is None:
                captured_style = current_style
        elif col < end and col + grapheme_w > start:
            output.append(fillchar * (min(end, col + grapheme_w) - max(start, col)))
            if propagate_sgr and captured_style is None:
                captured_style = current_style

        col += grapheme_w
        idx += len(grapheme)

    return ''.join(output), captured_style, end_style


def _text_sizing_clip(
    ts: TextSizing,
    col: int,
    start: int,
    end: int,
    fillchar: str,
    ambiguous_width: int,
    term_program: bool | str,
    write_cells: Callable[[str, int, int], None],
) -> int:
    """
    Emit tokens for a text-sizing (OSC 66) sequence, clipped to (start, end).

    Calls *write_cells(text, width, col)* for each emitted cell or sequence. Returns new column
    position.
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-positional-arguments,too-complex
    ts_width = ts.display_width(ambiguous_width)

    # Fully visible: emit entire sequence
    if col >= start and col + ts_width <= end:
        write_cells(ts.make_sequence(), ts_width, col)
        return col + ts_width
    # Fully outside: just advance column
    if col >= end or col + ts_width <= start:
        return col + ts_width

    # Partial overlap: decompose
    rel_start = max(0, start - col)
    rel_end = min(end, col + ts_width) - col
    scale = ts.params.scale

    units: list[tuple[str, int]] = []
    if ts.params.width > 0:
        for g in islice(iter_graphemes(ts.text), ts.params.width):
            units.append((g, scale))
        for _ in range(ts.params.width - len(units)):
            units.append(('', scale))
    else:
        for g in iter_graphemes(ts.text):
            units.append(
                (g, width(g, ambiguous_width=ambiguous_width,
                          term_program=term_program) * scale))

    pending_units: list[tuple[str, int]] = []

    def flush(flush_col: int) -> None:
        if not pending_units:
            return
        texts = [u[0] for u in pending_units]
        total_w = sum(u[1] for u in pending_units)
        params = TextSizingParams(
            scale,
            len(texts) if ts.params.width > 0 else 0,
            ts.params.numerator, ts.params.denominator,
            ts.params.vertical_align, ts.params.horizontal_align)
        write_cells(
            TextSizing(params, ''.join(texts), ts.terminator).make_sequence(),
            total_w,
            flush_col)
        pending_units.clear()

    flush_col_pos = col + rel_start
    unit_pos = 0
    for unit_text, unit_w in units:
        unit_end = unit_pos + unit_w
        if unit_end <= rel_start:
            unit_pos = unit_end
            continue
        if unit_pos >= rel_end:
            break

        overlap = min(unit_end, rel_end) - max(unit_pos, rel_start)
        if overlap == unit_w and unit_w > 0:
            if not pending_units:
                flush_col_pos = col + max(unit_pos, rel_start)
            pending_units.append((unit_text, unit_w))
        else:
            flush(flush_col_pos)
            abs_start = col + max(unit_pos, rel_start)
            for i in range(overlap):
                write_cells(fillchar, 1, abs_start + i)
        unit_pos = unit_end

    flush(flush_col_pos)
    return col + ts_width


def _clip_painter(
    text: str,
    start: int,
    end: int,
    *,
    propagate_sgr: bool,
    ambiguous_width: int,
    term_program: bool | str,
    fillchar: str,
    tabsize: int,
    control_codes: Literal['parse', 'strict', 'ignore'],
) -> tuple[str, Optional[_SGRState], Optional[_SGRState]]:
    """
    Clip text, painting cells so that cursor movement can overwrite them.

    Text with no cursor movement to resolve is clipped by _clip_simple() instead.

    Returns ``(result, captured_style, end_style)``.  The caller applies SGR wrapping.
    """
    # pylint: disable=too-complex,too-many-locals,too-many-branches
    # pylint: disable=too-many-statements,too-many-nested-blocks
    # code length and complexity traded for performance, to allow this to be used as a "hot path"

    strict = control_codes == 'strict'
    cells: dict[int, tuple[str, int]] = {}
    hyperlink_cells: set[int] = set()
    sequences: list[tuple[int, int, str]] = []
    seq_order = 0

    col = 0
    idx = 0
    # captured_style is a frozen snapshot of current_style taken at the first
    # visible character emitted within the clip window (start, end); it stays
    # None until that point.  current_style is continuously updated by SGR
    # sequences throughout the scan.
    #
    # When propagate_sgr is False, current_style (and therefore captured_style)
    # remain None, and SGR sequences pass through as literal text.
    captured_style: Optional[_SGRState] = None
    # end_style is the state after the last SGR sequence emitted *within* the
    # clip window; it decides the trailing reset.  None until such a sequence
    # is emitted, meaning captured_style is still in effect at the end.
    end_style: Optional[_SGRState] = None
    current_style = _SGR_STATE_DEFAULT if propagate_sgr else None
    # Next movement at or after the scan position, -1 when none is left.
    next_movement: Optional[int] = None

    def _write_cells(s: str, w: int, write_col: int,
                     is_hyperlink: bool = False) -> None:
        """Write *w* cells of text *s* at *write_col*, handling wide-char splitting."""
        nonlocal captured_style, seq_order
        if w == 0:
            # Zero-width: a cell here would be overwritten by the next write.
            if s:
                sequences.append((write_col, seq_order, s))
                seq_order += 1
                if propagate_sgr and captured_style is None:
                    captured_style = current_style
            return
        for offset in range(w):
            src_col = write_col + offset
            if src_col > 0 and cells.get(src_col - 1, ('', 0))[1] == 2:
                cells[src_col - 1] = (fillchar, 1)
                hyperlink_cells.discard(src_col - 1)
            if cells.get(src_col, ('', 0))[1] == 2:
                cells[src_col + 1] = (fillchar, 1)
                hyperlink_cells.discard(src_col + 1)
            cells.pop(src_col, None)
            hyperlink_cells.discard(src_col)
        cells[write_col] = (s, w)
        if is_hyperlink:
            for offset in range(w):
                hyperlink_cells.add(write_col + offset)
        if propagate_sgr and captured_style is None:
            captured_style = current_style

    while idx < len(text):
        char = text[idx]

        # Early exit: past visible region.
        if col >= end and char not in '\r\x08\t\x1b':
            # Movement right-of the window can still rewinds back into it.
            if next_movement is None or 0 <= next_movement < idx:
                # Any match starts with one of these, and rfind is far cheaper.
                if max(text.rfind('\x08'), text.rfind('\r'), text.rfind('\x1b')) < idx:
                    next_movement = -1
                else:
                    found = _HORIZONTAL_CURSOR_MOVEMENT.search(text, idx)
                    next_movement = -1 if found is None else found.end()
            if next_movement < 0:
                if captured_style is not None:
                    break
                next_esc = text.find('\x1b', idx + 1)
                if next_esc == -1:
                    break
                idx = next_esc
                continue

        if char == '\x1b':
            m = _SEQUENCE_CLASSIFY.match(text, idx)
            if not m:
                # Record lone ESC as a zero-width sequence at current column.
                sequences.append((col, seq_order, char))
                seq_order += 1
                idx += 1
                continue

            # SGR: update current_style.  Sequences before the first visible
            # emission are folded into the prefix synthesized by
            # _apply_sgr_wrap(); those inside the clip window are emitted at
            # their original position; those at or beyond *end* are dropped.
            if m.group('sgr_params') is not None and propagate_sgr and current_style is not None:
                current_style = _sgr_state_update(current_style, m.group())
                if captured_style is not None and col < end:
                    sequences.append((col, seq_order, m.group()))
                    seq_order += 1
                    end_style = current_style
                idx = m.end()
                continue

            # OSC 8 hyperlink.
            if hl_state := HyperlinkParams.parse(m.group()):
                r = _process_hyperlink(
                    text, start, end, fillchar, tabsize, ambiguous_width,
                    term_program,
                    control_codes,
                    params=hl_state, match_end=m.end(), col=col,
                )
                if r.action is _HyperlinkAction.NO_CLOSE:
                    sequences.append((col, seq_order, m.group()))
                    seq_order += 1
                    idx = m.end()
                elif r.action is _HyperlinkAction.EMPTY:
                    idx = r.close_end
                elif r.action is _HyperlinkAction.OUTSIDE:
                    col += r.inner_width
                    idx = r.close_end
                else:
                    sequences.append((col, seq_order, r.open_seq))
                    seq_order += 1
                    _write_cells(r.clipped_inner, r.clipped_width, col,
                                 is_hyperlink=True)
                    col += r.clipped_width
                    sequences.append((col, seq_order, r.close_seq))
                    seq_order += 1
                    # Inner text is clipped with propagate_sgr=False, so any SGR
                    # sequences it emits are verbatim: fold them into our state.
                    if propagate_sgr and current_style is not None:
                        for sgr_m in _SGR_PATTERN.finditer(r.clipped_inner):
                            current_style = _sgr_state_update(current_style, sgr_m.group())
                            end_style = current_style
                    col = r.hl_col_end
                    idx = r.close_end
                continue

            # OSC 66 Text Sizing.
            if (ts_meta := m.group('ts_meta')) is not None:
                ts_text = m.group('ts_text') or ''
                ts_term = m.group('ts_term')
                assert ts_term is not None
                ts = TextSizing(
                    TextSizingParams.from_params(ts_meta, control_codes=control_codes),
                    ts_text, ts_term)
                col = _text_sizing_clip(
                    ts, col, start, end, fillchar, ambiguous_width,
                    term_program,
                    _write_cells)
                idx = m.end()
                continue

            # Indeterminate-effect sequences: raise in strict mode.
            seq = m.group()
            if strict and INDETERMINATE_EFFECT_SEQUENCE.match(seq):
                raise ValueError(
                    f"Indeterminate cursor sequence at position {idx}, "
                    f"{seq!r}"
                )

            # Horizontal Position Absolute (CSI n G).
            if (hpa_n := m.group('hpa_n')) is not None:
                col = int(hpa_n) - 1 if hpa_n else 0
                idx = m.end()
                continue

            # Cursor Forward (CSI n C).
            if (cforward_n := m.group('cforward_n')) is not None:
                n_forward = int(cforward_n) if cforward_n else 1
                move_end = col + n_forward
                if col < end and move_end > start:
                    for i in range(max(col, start), min(move_end, end)):
                        _write_cells(fillchar, 1, i)
                col = move_end
                idx = m.end()
                continue

            # Cursor Backward (CSI n D).
            if (cbackward_n := m.group('cbackward_n')) is not None:
                n_backward = int(cbackward_n) if cbackward_n else 1
                if strict and n_backward > col:
                    raise ValueError(
                        f"Cursor left movement at position {idx} would move "
                        f"{n_backward} cells left from column {col}, "
                        f"exceeding string start"
                    )
                col -= n_backward
                if col < 0:
                    col = 0
                idx = m.end()
                continue

            # Any other recognized sequence: preserve as-is.
            sequences.append((col, seq_order, m.group()))
            seq_order += 1
            idx = m.end()
            continue

        # Carriage return.
        if char == '\r':
            col = 0
            idx += 1
            continue

        # Backspace.
        if char == '\x08':
            if col > 0:
                col -= 1
            idx += 1
            continue

        # Tab expansion.
        if char == '\t':
            if tabsize > 0:
                next_tab = col + (tabsize - (col % tabsize))
                for fill_col in range(max(col, start), min(next_tab, end)):
                    _write_cells(' ', 1, fill_col)
                col = next_tab
            elif start <= col < end:
                sequences.append((col, seq_order, '\t'))
                seq_order += 1
            idx += 1
            continue

        # Grapheme cluster.
        grapheme = next(iter_graphemes(text, start=idx))
        grapheme_w = width(grapheme, ambiguous_width=ambiguous_width,
                           term_program=term_program)

        # Emit grapheme or fillchar depending on visibility within clip window.
        if grapheme_w == 0:
            if start <= col < end:
                sequences.append((col, seq_order, grapheme))
                seq_order += 1
        elif col >= start and col + grapheme_w <= end:
            _write_cells(grapheme, grapheme_w, col)
        elif col < end and col + grapheme_w > start:
            clip_start = max(start, col)
            for offset in range(min(end, col + grapheme_w) - clip_start):
                _write_cells(fillchar, 1, clip_start + offset)

        col += grapheme_w
        idx += len(grapheme)

    return (_reconstruct_painter(cells, sequences, start, end, fillchar),
            captured_style, end_style)


def clip(
    text: str,
    start: int = 0,
    end: int = -1,
    *,
    fillchar: str = ' ',
    tabsize: int = 8,
    ambiguous_width: int = 1,
    propagate_sgr: bool = True,
    control_codes: Literal['parse', 'strict', 'ignore'] = 'parse',
    overtyping: Optional[bool] = None,
    term_program: bool | str = False,
) -> str:
    r"""
    Clip text to display columns (start, end) while preserving all terminal sequences.

    This function extracts a substring using visible column positions. Terminal escape sequences
    are preserved in output. If a wide character (width of 2) is
    split at a boundary, it is replaced with ``fillchar``.

    TAB characters (``\t``) are expanded to spaces up to the next tab stop, controlled by the
    ``tabsize`` parameter.  When cursor movement is detected, a "painter's algorithm" is used unless
    ``overtyping=False`` is set.  Cursor movement control codes are parsed for their effects instead
    of ignored.  For these operations, it is assumed that ``text`` begins at column 0.

    For text containing **OSC 8 hyperlinks**, the visible text inside a hyperlink is clipped to the
    requested column range and the hyperlink sequence is rebuilt::

        >>> clip('\x1b]8;;http://example.com\x07Click This link\x1b]8;;\x07', 6, 10)
        '\x1b]8;;http://example.com\x07This\x1b]8;;\x07'

    :param text: String to clip, may contain terminal escape sequences.
    :param start: Absolute starting column (inclusive, 0-indexed), default ``0``.
    :param end: Absolute ending column (exclusive).  The default value, ``-1``,
        signifies "to the end of the line", clipping only from *start* without
        requiring the caller to measure the display width of *text*.
    :param fillchar: Character to use when a wide character must be split at
        a boundary (default space). Must have display width of 1.
    :param tabsize: Tab stop width (default 8). Set to 0 to pass tabs through
        as zero-width (preserved in output but don't advance column position).
    :param ambiguous_width: Width to use for East Asian Ambiguous (A)
        characters. Default is ``1`` (narrow). Set to ``2`` for CJK contexts.
    :param propagate_sgr: If True (default), SGR (terminal styling) sequences
        are propagated, matching :func:`propagate_sgr`.  The result begins with
        any style active at the start position, retains any style changes
        occurring within the clipped region at their original position, and
        ends with a reset sequence if styles are active at the end position.
    :param control_codes: How to handle control characters and sequences:

        - ``'parse'`` (default): Track horizontal cursor movement and clip
          hyperlink text.  Cursor overwrite is always allowed, with best effort
          results; indeterminate sequences (home, clear, reset, etc.) are
          preserved as zero-width.
        - ``'strict'``: Like ``parse``, but raises :exc:`ValueError` on
          sequences with indeterminate effects (cursor home, clear screen,
          reset, vertical movement, etc.) matching :func:`width` behavior.
          Also raises on out-of-bounds horizontal cursor movement.
        - ``'ignore'``: All control characters are treated as zero-width.
          Cursor movement is not tracked (fastest path).

    :param overtyping: Whether to use the painter's algorithm for cursor
        movement (``\b`` backspace, ``\r`` carriage return, and CSI cursor
        left/right/position sequences).  When ``None`` (default), auto-detects
        by scanning for these characters in *text*.  Set to ``False`` for improved
        performance when the caller knows *text* contains no cursor movement
        characters.  Set to ``True`` to force the painter's algorithm (useful
        for testing).  Has no effect when ``control_codes='ignore'``.
    :param term_program: Terminal software identifier for table correction.
        ``False`` (default) disables override lookup.  ``True`` reads the
        ``TERM_PROGRAM`` or ``TERM`` environment variable for auto-detection.
        Accepts a canonical terminal name matching :func:`list_term_programs`,
        such as from XTVERSION_, ENQ_, or ``TERM_PROGRAM``.

        .. versionadded:: 0.8.0

    :returns: Substring of ``text`` spanning display columns (start, end),
        with all terminal sequences preserved and wide characters at boundaries
        replaced with ``fillchar``.

    :raises ValueError: If ``end`` is negative and not ``-1``, or if
        ``control_codes='strict'`` and an indeterminate-effect sequence or
        out-of-bounds cursor movement is encountered.

    SGR (terminal styling) sequences are propagated by default. The result
    begins with any active style and ends with a reset::

        >>> clip('\x1b[1;34mHello world\x1b[0m', 6, 11)
        '\x1b[1;34mworld\x1b[0m'
        >>> clip('\x1b[1mbold\x1b[m normal', 1, 9)
        '\x1b[1mold\x1b[m norm'

    Set ``propagate_sgr=False`` to disable this behavior.

    .. note::

       Segmentation follows UAX #29 grapheme clusters. Tamil, Kannada and Sinhala may be clipped
       short of ``end`` and leave a bare virama at the boundary. Correct rendering of these
       languages is not specified by unicode.org standards, and no terminal emulator or editor
       handles them legibly, so this library function makes no attempt at accommodating them.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.5.0
       Added ``propagate_sgr`` parameter (default True).

    .. versionchanged:: 0.7.0
       Added ``control_codes`` parameter (default 'parse').
       OSC 8 hyperlink-aware clipping.  OSC 66 text sizing protocol support.
       Added ``overtyping`` parameter (default None, auto-detect).

    .. versionchanged:: 0.8.4
       ``start`` now defaults to ``0`` and ``end`` to ``-1``, meaning "to the
       end of the line"::

           >>> clip('\x1b[1;34mHello world\x1b[0m', 6)
           '\x1b[1;34mworld\x1b[0m'

    Example::

        >>> clip('hello world', 0, 5)
        'hello'
        >>> clip('中文字', 0, 3)  # Wide char split at column 3
        '中 '
        >>> clip('a\tb', 0, 10)  # Tab expanded to spaces
        'a       b'
    """
    start = max(start, 0)
    if end < 0:
        if end != -1:
            raise ValueError(
                f"end must be -1 (to end of line) or non-negative, got {end}")
        # Unbounded: clip only from *start*, to the end of the line.
        end = sys.maxsize
    if end <= start:
        return ''

    # Fast path: printable ASCII only.
    if text.isascii() and text.isprintable():
        return text[start:end]

    # Offload to libwcwidth, which reports an unsupported sequence rather than
    # answering differently.  Only the options are tested here, never the text.
    if (_c_clip is not None
            and control_codes == 'parse'
            and overtyping is not True
            and tabsize > 0
            and len(fillchar) == 1 and fillchar.isascii()):
        result = _c_clip(
            text, start, end, fillchar=fillchar, tabsize=tabsize,
            ambiguous_width=ambiguous_width, propagate_sgr=propagate_sgr,
            control_codes=control_codes, term_program=term_program)
        if result is not None:
            return result

    ambiguous_width = _clamp_ambiguous_width(ambiguous_width)

    # No escape sequences => no SGR tracking needed.
    has_esc = '\x1b' in text
    if propagate_sgr and not has_esc:
        propagate_sgr = False

    # Determine whether painter's algorithm is needed.
    if overtyping is None:
        # Auto-detect: scan for cursor movement characters.
        overtyping = (
            control_codes != 'ignore' and
            ('\x08' in text or '\r' in text or
             (has_esc and bool(_HORIZONTAL_CURSOR_MOVEMENT.search(text))))
        )
    elif overtyping and control_codes == 'ignore':
        overtyping = False  # control_codes='ignore' overrides

    if overtyping:
        return _apply_sgr_wrap(*_clip_painter(
            text=text,
            start=start,
            end=end,
            propagate_sgr=propagate_sgr,
            ambiguous_width=ambiguous_width,
            term_program=term_program,
            fillchar=fillchar,
            tabsize=tabsize,
            control_codes=control_codes,
        ))

    return _apply_sgr_wrap(*_clip_simple(
        text=text,
        start=start,
        end=end,
        propagate_sgr=propagate_sgr,
        ambiguous_width=ambiguous_width,
        term_program=term_program,
        fillchar=fillchar,
        tabsize=tabsize,
        control_codes=control_codes,
    ))
