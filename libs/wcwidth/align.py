"""Python grapheme, emoji, and sequence-aware ljust, rjust, center()."""
from __future__ import annotations

from typing import Literal

# local
from ._width import width


def ljust(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: Literal['parse', 'strict', 'ignore'] = 'parse',
    ambiguous_width: int = 1,
    term_program: bool | str = False,
) -> str:
    r"""
    Return text left-justified in a string of given display width.

    :param text: String to justify, may contain terminal sequences.
    :param dest_width: Desired displayed width of result in terminal cells, which
        ``text`` can exceed. Use :func:`wcwidth.clip` to ensure ``text`` does not
        exceed ``dest_width``.
    :param fillchar: Single character for padding (default space). Must have
        display width of 1. Unicode characters like ``'·'`` are acceptable.
        The width is not validated.
    :param control_codes: How to handle control sequences when measuring.
        Passed to :func:`width` for measurement.
    :param ambiguous_width: Width to use for East Asian Ambiguous (A)
        characters. Default is ``1`` (narrow). Set to ``2`` for CJK contexts.
    :param term_program: Terminal software identifier for table correction.
        ``False`` (default) disables override lookup.  ``True`` reads the
        ``TERM_PROGRAM`` or ``TERM`` environment variable for auto-detection.
        Accepts a canonical terminal name matching :func:`list_term_programs`,
        such as from XTVERSION_, ENQ_, or ``TERM_PROGRAM``.

        .. versionadded:: 0.8.0
    :returns: Text padded on the right to reach ``dest_width``.

    Tabs are measured as though ``text`` begins at column 0. It is suggested to first use
    :func:`str.expandtabs` or :func:`wcwidth.clip` to expand tabs before applying text alignment.

    Text wider than ``dest_width`` is returned unchanged. Clip to ``dest_width`` if needed::

        >>> from wcwidth import clip
        >>> ljust('abcdefghi', 2)              # wider than dest_width, unchanged
        'abcdefghi'
        >>> ljust(clip('abcdefghi', 0, 2), 2)  # clipped to dest_width
        'ab'

    .. versionadded:: 0.3.0

    Example::

        >>> ljust('hi', 5)
        'hi   '
        >>> ljust('\x1b[31mhi\x1b[0m', 5)
        '\x1b[31mhi\x1b[0m   '
        >>> ljust('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6)
        '👨‍👩‍👧    '
        >>> ljust('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6, term_program='VTE')
        '👨\u200d👩\u200d👧'
    """
    if text.isascii() and text.isprintable():
        text_width = len(text)
    else:
        text_width = width(text, control_codes=control_codes, ambiguous_width=ambiguous_width,
                           term_program=term_program)
    padding_cells = max(0, dest_width - text_width)
    return text + fillchar * padding_cells


def rjust(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: Literal['parse', 'strict', 'ignore'] = 'parse',
    ambiguous_width: int = 1,
    term_program: bool | str = False,
) -> str:
    r"""
    Return text right-justified in a string of given display width.

    :param text: String to justify, may contain terminal sequences.
    :param dest_width: Desired displayed width of result in terminal cells, which ``text`` can
        exceed. Use :func:`wcwidth.clip` to ensure ``text`` does not exceed ``dest_width``.
    :param fillchar: Single character for padding (default space). Must have
        display width of 1. Unicode characters like ``'·'`` are acceptable.
        The width is not validated.
    :param control_codes: How to handle control sequences when measuring.
        Passed to :func:`width` for measurement.
    :param ambiguous_width: Width to use for East Asian Ambiguous (A)
        characters. Default is ``1`` (narrow). Set to ``2`` for CJK contexts.
    :param term_program: Terminal software identifier for table correction.
        ``False`` (default) disables override lookup.  ``True`` reads the
        ``TERM_PROGRAM`` or ``TERM`` environment variable for auto-detection.
        Accepts a canonical terminal name matching :func:`list_term_programs`,
        such as from XTVERSION_, ENQ_, or ``TERM_PROGRAM``.

        .. versionadded:: 0.8.0
    :returns: Text padded on the left to reach ``dest_width``.

    Tabs are measured as though ``text`` begins at column 0. The ``fillchar`` placed before a tab by
    right-justified text moves any tabs to a later stop and produces an incorrect alignment result.
    It is suggested never to align text containing a tab, calling :func:`str.expandtabs` or
    :func:`wcwidth.clip` (which also expands tabs) if necessary::

        >>> rjust('a\tbc', 12)                # when displayed, becomes width of 10, wrong
        '  a\tbc'
        >>> rjust('a\tbc'.expandtabs(), 12)   # properly displayed as width of 12
        '  a       bc'

    Text wider than ``dest_width`` is returned unchanged. Clip to ``dest_width`` if needed::

        >>> from wcwidth import clip
        >>> rjust('abcdefghi', 2)              # wider than dest_width, unchanged
        'abcdefghi'
        >>> rjust(clip('abcdefghi', 0, 2), 2)  # clipped to dest_width
        'ab'

    .. versionadded:: 0.3.0

    Example::

        >>> rjust('hi', 5)
        '   hi'
        >>> rjust('\x1b[31mhi\x1b[0m', 5)
        '   \x1b[31mhi\x1b[0m'
        >>> rjust('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6)
        '    👨‍👩‍👧'
        >>> rjust('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6, term_program='VTE')
        '👨\u200d👩\u200d👧'
    """
    if text.isascii() and text.isprintable():
        text_width = len(text)
    else:
        text_width = width(text, control_codes=control_codes, ambiguous_width=ambiguous_width,
                           term_program=term_program)
    padding_cells = max(0, dest_width - text_width)
    return fillchar * padding_cells + text


def center(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: Literal['parse', 'strict', 'ignore'] = 'parse',
    ambiguous_width: int = 1,
    term_program: bool | str = False,
) -> str:
    r"""
    Return text centered in a string of given display width.

    :param text: String to center, may contain terminal sequences.
    :param dest_width: Desired displayed width of result in terminal cells, which
        ``text`` can exceed. Use :func:`wcwidth.clip` to ensure ``text`` does not
        exceed ``dest_width``.
    :param fillchar: Single character for padding (default space). Must have
        display width of 1. Unicode characters like ``'·'`` are acceptable.
        The width is not validated.
    :param control_codes: How to handle control sequences when measuring.
        Passed to :func:`width` for measurement.
    :param ambiguous_width: Width to use for East Asian Ambiguous (A)
        characters. Default is ``1`` (narrow). Set to ``2`` for CJK contexts.
    :param term_program: Terminal software identifier for table correction.
        ``False`` (default) disables override lookup.  ``True`` reads the
        ``TERM_PROGRAM`` or ``TERM`` environment variable for auto-detection.
        Accepts a canonical terminal name matching :func:`list_term_programs`,
        such as from XTVERSION_, ENQ_, or ``TERM_PROGRAM``.

        .. versionadded:: 0.8.0
    :returns: Text padded on both sides to reach ``dest_width``.

    For odd-width padding, the extra cell fills in the same cell position as
    Python's :meth:`str.center` behavior (the left side when ``dest_width`` is
    odd, the right side when ``dest_width`` is even).
    See `the eccentric str.center <https://jazcap53.github.io/pythons-eccentric-strcenter.html>`_.

    Tabs are measured as though ``text`` begins at column 0. The ``fillchar`` placed before a tab by
    centered text moves any tabs to a later stop and produces an incorrect alignment result. It is
    suggested never to align text containing a tab, calling :func:`str.expandtabs` or
    :func:`wcwidth.clip` (which also expands tabs) if necessary::

        >>> center('a\tbc', 12)               # when displayed, becomes width of 11, wrong
        ' a\tbc '
        >>> center('a\tbc'.expandtabs(), 12)  # properly displayed as width of 12
        ' a       bc '

    Text wider than ``dest_width`` is returned unchanged. Clip to ``dest_width`` if needed::

        >>> from wcwidth import clip
        >>> center('abcdefghi', 2)              # wider than dest_width, unchanged
        'abcdefghi'
        >>> center(clip('abcdefghi', 0, 2), 2)  # clipped to dest_width
        'ab'

    .. versionadded:: 0.3.0

    Example::

        >>> center('hi', 6)
        '  hi  '
        >>> center('\x1b[31mhi\x1b[0m', 6)
        '  \x1b[31mhi\x1b[0m  '
        >>> center('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6)
        '  👨‍👩‍👧  '
        >>> center('\U0001F468\u200D\U0001F469\u200D\U0001F467', 6, term_program='VTE')
        '👨\u200d👩\u200d👧'
    """
    if text.isascii() and text.isprintable():
        text_width = len(text)
    else:
        text_width = width(text, control_codes=control_codes, ambiguous_width=ambiguous_width,
                           term_program=term_program)
    total_padding = max(0, dest_width - text_width)
    # matching https://jazcap53.github.io/pythons-eccentric-strcenter.html
    left_pad = total_padding // 2 + (total_padding & dest_width & 1)
    right_pad = total_padding - left_pad
    return fillchar * left_pad + text + fillchar * right_pad
