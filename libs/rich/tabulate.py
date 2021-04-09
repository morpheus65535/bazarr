from collections.abc import Mapping
from typing import Optional

from rich.console import JustifyMethod

from . import box
from .highlighter import ReprHighlighter
from .pretty import Pretty
from .table import Table


def tabulate_mapping(
    mapping: Mapping,
    title: str = None,
    caption: str = None,
    title_justify: Optional[JustifyMethod] = None,
    caption_justify: Optional[JustifyMethod] = None,
) -> Table:
    """Generate a simple table from a mapping.

    Args:
        mapping (Mapping): A mapping object (e.g. a dict);
        title (str, optional): Optional title to be displayed over the table.
        caption (str, optional): Optional caption to be displayed below the table.
        title_justify (str, optional): Justify method for title. Defaults to None.
        caption_justify (str, optional): Justify method for caption. Defaults to None.

    Returns:
        Table: A table instance which may be rendered by the Console.
    """
    table = Table(
        show_header=False,
        title=title,
        caption=caption,
        box=box.ROUNDED,
        border_style="blue",
    )
    table.title = title
    table.caption = caption
    if title_justify is not None:
        table.title_justify = title_justify
    if caption_justify is not None:
        table.caption_justify = caption_justify
    highlighter = ReprHighlighter()
    for key, value in mapping.items():
        table.add_row(
            Pretty(key, highlighter=highlighter), Pretty(value, highlighter=highlighter)
        )
    return table
