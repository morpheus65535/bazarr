#!/usr/bin/env python
from __future__ import annotations

from typing import Any

from ..utils import extend_safe


def test_extend_safe_hashable() -> None:
    target = [1, 2]
    extend_safe(target, [2, 3, 3, 4])
    assert target == [1, 2, 3, 4]


def test_extend_safe_unhashable() -> None:
    # Unhashable elements (e.g. introspected list/dict property values) must
    # still be deduplicated via linear membership instead of raising.
    target: list[Any] = [["a"]]
    extend_safe(target, [["a"], ["b"], ["b"]])
    assert target == [["a"], ["b"]]


def test_extend_safe_mixed_falls_back_without_duplicating() -> None:
    # Hashable elements go through the fast set path; the first unhashable one
    # switches to the linear fallback, and already-added elements are not
    # appended twice.
    target: list[Any] = [1]
    extend_safe(target, [1, 2, ["x"], ["x"], 2])
    assert target == [1, 2, ["x"]]
