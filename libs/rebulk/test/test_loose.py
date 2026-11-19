#!/usr/bin/env python

from __future__ import annotations

from ..loose import call


def test_loose_function() -> None:
    def func(v1: int, v2: int, v3: int = 3, v4: int = 4) -> int:
        return v1 + v2 + v3 + v4

    assert call(func, 1, 2) == func(1, 2)
    assert call(func, 1, 2, 3, 5) == func(1, 2, 3, 5)
    assert call(func, 1, 2, v3=4, v4=5) == func(1, 2, v3=4, v4=5)
    assert call(func, 1, 2, 3, 4, 5) == func(1, 2, 3, 4)
    assert call(func, 1, 2, 3, 4, more=5) == func(1, 2, 3, 4)


def test_loose_varargs_function() -> None:
    def func(v1: int, v2: int, *args: int) -> int:
        return v1 + v2 + args[0] if len(args) > 0 else 3 + args[1] if len(args) > 1 else 4

    assert call(func, 1, 2) == func(1, 2)
    assert call(func, 1, 2, 3, 5) == func(1, 2, 3, 5)
    assert call(func, 1, 2, 3, 4, 5) == func(1, 2, 3, 4)


def test_loose_kwargs_function() -> None:
    def func(v1: int, v2: int, **kwargs: int) -> int:
        return v1 + v2 + kwargs.get("v3", 3) + kwargs.get("v4", 4)

    assert call(func, v1=1, v2=2) == func(v1=1, v2=2)
    assert call(func, v1=1, v2=2, v3=3, v4=5) == func(v1=1, v2=2, v3=3, v4=5)


def test_loose_class() -> None:
    class Dummy:
        def __init__(self, v1: int, v2: int, v3: int = 3, v4: int = 4) -> None:
            self.v1 = v1
            self.v2 = v2
            self.v3 = v3
            self.v4 = v4

        def call(self) -> int:
            return self.v1 + self.v2 + self.v3 + self.v4

    assert call(Dummy, 1, 2).call() == Dummy(1, 2).call()
    assert call(Dummy, 1, 2, 3, 5).call() == Dummy(1, 2, 3, 5).call()
    assert call(Dummy, 1, 2, v3=4, v4=5).call() == Dummy(1, 2, v3=4, v4=5).call()
    assert call(Dummy, 1, 2, 3, 4, 5).call() == Dummy(1, 2, 3, 4).call()
    assert call(Dummy, 1, 2, 3, 4, more=5).call() == Dummy(1, 2, 3, 4).call()


def test_loose_varargs_class() -> None:
    class Dummy:
        def __init__(self, v1: int, v2: int, *args: int) -> None:
            self.v1 = v1
            self.v2 = v2
            self.v3 = args[0] if len(args) > 0 else 3
            self.v4 = args[1] if len(args) > 1 else 4

        def call(self) -> int:
            return self.v1 + self.v2 + self.v3 + self.v4

    assert call(Dummy, 1, 2).call() == Dummy(1, 2).call()
    assert call(Dummy, 1, 2, 3, 5).call() == Dummy(1, 2, 3, 5).call()
    assert call(Dummy, 1, 2, 3, 4, 5).call() == Dummy(1, 2, 3, 4).call()


def test_loose_kwargs_class() -> None:
    class Dummy:
        def __init__(self, v1: int, v2: int, **kwargs: int) -> None:
            self.v1 = v1
            self.v2 = v2
            self.v3 = kwargs.get("v3", 3)
            self.v4 = kwargs.get("v4", 4)

        def call(self) -> int:
            return self.v1 + self.v2 + self.v3 + self.v4

    assert call(Dummy, v1=1, v2=2).call() == Dummy(v1=1, v2=2).call()
    assert call(Dummy, v1=1, v2=2, v3=3, v4=5).call() == Dummy(v1=1, v2=2, v3=3, v4=5).call()
