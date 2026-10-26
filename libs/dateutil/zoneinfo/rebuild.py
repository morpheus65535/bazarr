import warnings

__all__ = ["rebuild", "RebuildDeprecationWarning"]


class RebuildDeprecationWarning(FutureWarning):
    """Warning raised by :func:`rebuild`, which no longer does anything.

    A warnings filter turns this into an error by default. To keep calling
    :func:`rebuild` as a no-op, filter it out, e.g.::

        warnings.filterwarnings(
            "ignore", category=dateutil.zoneinfo.rebuild.RebuildDeprecationWarning
        )
    """


def rebuild(filename, tag=None, format="gz", zonegroups=[], metadata=None):
    """Formerly rebuilt the zoneinfo tarball bundled with ``dateutil``.

    ``dateutil`` no longer ships a zoneinfo tarball; it reads time zone data
    from the system and from the `tzdata <https://pypi.org/project/tzdata/>`_
    package instead. This function now does nothing except raise
    :class:`RebuildDeprecationWarning`, which is an error unless a warnings
    filter says otherwise.

    .. deprecated:: 3.0.0
    """
    # The filter is added at call time rather than at import time, so that it
    # is still in place if the module was first imported inside a
    # warnings.catch_warnings() block. It is appended, so any filter the user
    # has installed for this category takes precedence.
    warnings.filterwarnings(
        "error", category=RebuildDeprecationWarning, append=True
    )
    warnings.warn(
        "dateutil.zoneinfo.rebuild() no longer does anything, because dateutil "
        "no longer ships a zoneinfo tarball. Use the tzdata package or the "
        "system time zone data instead.",
        RebuildDeprecationWarning,
        stacklevel=2,
    )
