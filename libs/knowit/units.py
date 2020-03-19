# -*- coding: utf-8 -*-


def _build_unit_registry():
    try:
        from pint import UnitRegistry

        registry = UnitRegistry()
        registry.define('FPS = 1 * hertz')
    except ImportError:
        class NoUnitRegistry:

            def __init__(self):
                pass

            def __getattr__(self, item):
                return 1

        registry = NoUnitRegistry()

    return registry


units = _build_unit_registry()
