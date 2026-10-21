#!/usr/bin/env python
"""
Groups markers (...), [...] and {...}
"""

from __future__ import annotations

from typing import Any

from rebulk import Rebulk

from ...options import ConfigurationException


def groups(config: dict[str, Any]) -> Rebulk:
    """
    Builder for rebulk object.

    :param config: rule configuration
    :type config: dict
    :return: Created Rebulk object
    :rtype: Rebulk
    """
    rebulk = Rebulk()
    rebulk.defaults(name="group", marker=True)

    starting = config["starting"]
    ending = config["ending"]

    if len(starting) != len(ending):
        raise ConfigurationException("Starting and ending groups must have the same length")

    def mark_groups(input_string: str) -> list[tuple[int, int]]:
        """
        Functional pattern to mark groups (...), [...] and {...}.

        :param input_string:
        :return:
        """
        openings: tuple[list[int], ...] = ([],) * len(starting)

        ret: list[tuple[int, int]] = []
        for i, char in enumerate(input_string):
            start_type = starting.find(char)
            if start_type > -1:
                openings[start_type].append(i)

            end_type = ending.find(char)
            if end_type > -1:
                try:
                    start_index = openings[end_type].pop()
                    ret.append((start_index, i + 1))
                except IndexError:
                    pass
        return ret

    rebulk.functional(mark_groups)
    return rebulk
