from abc import ABC, abstractmethod


class Pager(ABC):
    """Base class for a pager."""

    @abstractmethod
    def show(self, content: str) -> None:
        """Show content in pager.

        Args:
            content (str): Content to be displayed.
        """


class SystemPager(Pager):
    """Uses the pager installed on the system."""

    _pager = lambda self, content: __import__("pydoc").pager(content)

    def show(self, content: str) -> None:
        """Use the same pager used by pydoc."""
        self._pager(content)


if __name__ == "__main__":  # pragma: no cover
    from .__main__ import make_test_card
    from .console import Console

    console = Console()
    with console.pager(styles=True):
        console.print(make_test_card())
