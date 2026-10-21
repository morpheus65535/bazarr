# pylint: disable=missing-module-docstring,missing-function-docstring
# pylint: disable=unused-argument,redefined-outer-name

from typing import Union, Literal, Iterator, Optional, Sequence

TermProgram = Union[bool, str]
ControlCodes = Literal['parse', 'strict', 'ignore']


def wcwidth(wc: str, unicode_version: str = 'auto', ambiguous_width: int = 1) -> int: ...
def wcswidth(
    pwcs: str,
    n: Optional[int] = None,
    unicode_version: str = 'auto',
    ambiguous_width: int = 1,
) -> int: ...
def wcstwidth(
    pwcs: str,
    n: Optional[int] = None,
    unicode_version: str = 'auto',
    ambiguous_width: int = 1,
    term_program: TermProgram = True,
) -> int: ...
def width(
    text: str,
    *,
    control_codes: ControlCodes = 'parse',
    tabsize: int = 8,
    ambiguous_width: int = 1,
    term_program: TermProgram = False,
) -> int: ...
def ljust(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: ControlCodes = 'parse',
    ambiguous_width: int = 1,
    term_program: TermProgram = False,
) -> str: ...
def rjust(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: ControlCodes = 'parse',
    ambiguous_width: int = 1,
    term_program: TermProgram = False,
) -> str: ...
def center(
    text: str,
    dest_width: int,
    fillchar: str = ' ',
    *,
    control_codes: ControlCodes = 'parse',
    ambiguous_width: int = 1,
    term_program: TermProgram = False,
) -> str: ...
def clip(
    text: str,
    start: int,
    end: int,
    *,
    fillchar: str = ' ',
    tabsize: int = 8,
    ambiguous_width: int = 1,
    propagate_sgr: bool = True,
    control_codes: ControlCodes = 'parse',
    term_program: TermProgram = False,
) -> Optional[str]: ...
def strip_sequences(text: str) -> str: ...
def propagate_sgr(lines: Sequence[str]) -> list[str]: ...
def iter_graphemes(
    unistr: str,
    start: int = 0,
    end: Optional[int] = None,
) -> Iterator[str]: ...
