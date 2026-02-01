from dataclasses import dataclass
from typing import Tuple, Union, Optional, Dict, Iterable, Iterator
from enum import IntEnum
import xml.etree.ElementTree as ET
from contextlib import contextmanager


@dataclass(init=False)
class Color:
    """
    8-bit RGB color with alpha channel.

    All values are ints from 0 to 255.
    """
    r: int
    g: int
    b: int
    a: int = 0

    def __init__(self, r: int, g: int, b: int, a: int = 0):
        for value in r, g, b, a:
            if value not in range(256):
                raise ValueError("Color channels must have values 0-255")

        self.r = r
        self.g = g
        self.b = b
        self.a = a


class Alignment(IntEnum):
    """
    An integer enum specifying text alignment

    The integer values correspond to Advanced SubStation Alpha definition (like on numpad).
    Note that the older SubStation Alpha (SSA) specification used different numbering schema.

    """
    BOTTOM_LEFT = 1
    BOTTOM_CENTER = 2
    BOTTOM_RIGHT = 3
    MIDDLE_LEFT = 4
    MIDDLE_CENTER = 5
    MIDDLE_RIGHT = 6
    TOP_LEFT = 7
    TOP_CENTER = 8
    TOP_RIGHT = 9

    @classmethod
    def from_ssa_alignment(cls, alignment: int) -> "Alignment":
        """Convert SSA alignment to ASS alignment"""
        return Alignment(SSA_ALIGNMENT.index(alignment) + 1)

    def to_ssa_alignment(self) -> int:
        """Convert ASS alignment to SSA alignment"""
        return SSA_ALIGNMENT[self.value - 1]


SSA_ALIGNMENT: Tuple[int, ...] = (1, 2, 3, 9, 10, 11, 5, 6, 7)


#: Version of the pysubs2 library.
VERSION = "1.8.0"


IntOrFloat = Union[int, float]


def etree_iter_child_nodes(elem: ET.Element) -> Iterator[Union[ET.Element, str]]:
    """
    Yield child text nodes (as str) and subelements for given XML element

    Workaround for awkward ``xml.etree.ElementTree`` API.

    See also:
        `etree_append_child_nodes()`

    """
    if elem.text:
        yield elem.text
    for child_elem in elem:
        yield child_elem
        if child_elem.tail:
            yield child_elem.tail


def etree_append_child_nodes(elem: ET.Element, nodes: Iterable[Union[ET.Element, str]]) -> None:
    """
    Add child text nodes and subelements to given XML element

    See also:
        `etree_iter_child_nodes()`

    """
    last_child = elem[-1] if len(elem) > 0 else None
    for node in nodes:
        if isinstance(node, str):
            if last_child is None:
                if elem.text is None:
                    elem.text = node
                else:
                    elem.text += node
            else:
                if last_child.tail is None:
                    last_child.tail = node
                else:
                    last_child.tail += node
        else:
            elem.append(node)
            last_child = node


@contextmanager
def etree_register_namespace_override() -> Iterator[None]:
    """
    Context manager that reverts global changes from ``xml.etree.ElementTree.register_namespace()``

    Workaround for poor namespace handling in ``xml.etree.ElementTree``.

    """
    namespace_map: Optional[Dict[str, str]] = None
    namespace_map_original_content = {}
    try:
        namespace_map = getattr(ET.register_namespace, "_namespace_map", None)
        if namespace_map is not None:
            namespace_map_original_content = namespace_map.copy()
    except Exception:
        pass

    yield

    try:
        if namespace_map is not None:
            namespace_map.clear()
            namespace_map.update(namespace_map_original_content)
    except Exception:
        pass
