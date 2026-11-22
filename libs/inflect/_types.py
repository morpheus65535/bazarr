"""Types shared by the runtime and static interfaces."""

from typing import TYPE_CHECKING, Annotated, Any

if TYPE_CHECKING:  # pragma: no cover
    Word = Annotated[str, "String with at least 1 character"]
else:

    class _WordMeta(type):  # Too dynamic to be supported by mypy...
        def __instancecheck__(self, instance: Any) -> bool:
            return isinstance(instance, str) and len(instance) >= 1

    class Word(metaclass=_WordMeta):
        """String with at least 1 character"""

    # Keep the public class identity stable after moving its implementation out
    # of ``inflect.__init__``.  This also preserves the qualified name in
    # typeguard's error messages and in serialized values.
    Word.__module__ = "inflect"
