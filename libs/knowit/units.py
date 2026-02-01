import logging
import typing

logger = logging.getLogger(__name__)


class NullRegistry:
    """A NullRegistry that masquerades as a pint.UnitRegistry."""

    def __init__(self):
        """Initialize a null registry."""

    def __getattr__(self, item: typing.Any) -> int:
        """Return a Scalar 1 to simulate a unit."""
        return 1

    def __call__(self, value: str) -> float:
        """Try converting to int, to float and fallback to a scalar 1.0."""
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                pass
        return 1

    def __bool__(self):
        """Return False since a NullRegistry is not a pint.UnitRegistry."""
        return False

    def define(self, *args, **kwargs):
        """Pretend to add unit to the registry."""


def _build_unit_registry():
    try:
        import pint

        registry = pint.UnitRegistry()
        registry.define('FPS = 1 * hertz')

        pint.set_application_registry(registry)
        return registry
    except ModuleNotFoundError:
        pass
    except Exception:
        logger.exception("Cannot import the pint package")

    return NullRegistry()


units = _build_unit_registry()
