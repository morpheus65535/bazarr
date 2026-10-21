#!/usr/bin/env python
"""
Path markers
"""

from __future__ import annotations

from typing import Any

from rebulk import Rebulk
from rebulk.utils import find_all


def path(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()
    rebulk.defaults(name="path", marker=True)

    def mark_path(input_string: str, context: dict[str, Any]) -> list[tuple[int, int]]:
        """
        Functional pattern to mark path elements.

        :param input_string:
        :param context:
        :return:
        """
        ret: list[tuple[int, int]] = []
        if context.get("name_only", False):
            ret.append((0, len(input_string)))
        else:
            indices = list(find_all(input_string, "/"))
            indices += list(find_all(input_string, "\\"))
            indices += [-1, len(input_string)]

            indices.sort()

            for i in range(len(indices) - 1):
                ret.append((indices[i] + 1, indices[i + 1]))

        return ret

    rebulk.functional(mark_path)
    return rebulk
