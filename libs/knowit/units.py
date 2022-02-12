import typing

try:
    import pint
except ImportError:
    pint = False


class NullRegistry:
    """A NullRegistry that masquerades as a pint.UnitRegistry."""

    def __init__(self):
        """Initialize a null registry."""

    def __getattr__(self, item: typing.Any) -> int:
        """Return a Scalar 1 to simulate a unit."""
        return 1

    def __bool__(self):
        """Return False since a NullRegistry is not a pint.UnitRegistry."""
        return False

    def define(self, *args, **kwargs):
        """Pretend to add unit to the registry."""


def _build_unit_registry():
    registry = pint.UnitRegistry() if pint else NullRegistry()
    registry.define('FPS = 1 * hertz')
    return registry


units = _build_unit_registry()
