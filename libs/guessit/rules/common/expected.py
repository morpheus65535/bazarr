#!/usr/bin/env python
"""
Expected property factory
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rebulk import Rebulk
from rebulk.remodule import re
from rebulk.utils import find_all

from . import dash, seps

if TYPE_CHECKING:
    from collections.abc import Callable


def build_expected_function(context_key: str) -> Callable[[str, dict[str, Any]], list[Any]]:
    """
    Creates a expected property function
    :param context_key:
    :type context_key:
    :param cleanup:
    :type cleanup:
    :return:
    :rtype:
    """

    def expected(input_string: str, context: dict[str, Any]) -> list[Any]:
        """
        Expected property functional pattern.
        :param input_string:
        :type input_string:
        :param context:
        :type context:
        :return:
        :rtype:
        """
        ret: list[Any] = []
        for search in context.get(context_key) or ():
            if search.startswith("re:"):
                search = search[3:]
                search = search.replace(" ", "-")
                matches = (
                    Rebulk().regex(search, abbreviations=[dash], flags=re.IGNORECASE).matches(input_string, context)
                )
                for match in matches:
                    ret.append(match.span)
            else:
                for sep in seps:
                    input_string = input_string.replace(sep, " ")
                    search = search.replace(sep, " ")
                for start in find_all(input_string, search, ignore_case=True):
                    end = start + len(search)
                    value = input_string[start:end]
                    ret.append({"start": start, "end": end, "value": value})
        return ret

    return expected
