try:
    import zoneinfo

    reset_tzpath = zoneinfo.reset_tzpath
    InvalidTZPathWarning = zoneinfo.InvalidTZPathWarning

    def __getattr__(name):
        if name == "TZPATH":
            return zoneinfo.TZPATH
        else:
            raise AttributeError(
                "Module %s has no attribute %s" % (repr(__name__), repr(name))
            )

except ImportError:
    import os
    import sys
    import warnings

    import six

    class InvalidTZPathWarning(RuntimeWarning):
        """Warning raised if an invalid path is specified in PYTHONTZPATH."""

    def _parse_python_tzpath(env_var, stacklevel):
        if not env_var:
            return ()

        raw_tzpath = env_var.split(os.pathsep)
        new_tzpath = tuple(filter(os.path.isabs, raw_tzpath))

        # If anything has been filtered out, we will warn about it
        if len(new_tzpath) != len(raw_tzpath):
            msg = _get_invalid_paths_message(raw_tzpath)

            warnings.warn(
                "Invalid paths specified in PYTHONTZPATH environment variable. "
                + msg,
                InvalidTZPathWarning,
                stacklevel=stacklevel,
            )

        return new_tzpath

    def _get_invalid_paths_message(tzpaths):
        invalid_paths = (path for path in tzpaths if not os.path.isabs(path))

        prefix = "\n    "
        indented_str = prefix + prefix.join(invalid_paths)

        return (
            "Paths should be absolute but found the following relative paths:"
            + indented_str
        )

    def _reset_tzpath(to=None, stacklevel=4):
        global TZPATH
        tzpaths = to
        if tzpaths is not None:
            if isinstance(tzpaths, six.string_types + (bytes,)):
                raise TypeError(
                    "tzpaths must be a sequence, not %s: %s"
                    % (
                        type(tzpaths),
                        repr(tzpaths),
                    )
                )

            # Path-like objects not supported by os.path operations before 3.6
            if sys.version_info < (3, 6):
                tzpaths = tuple(map(str, tzpaths))

            if not all(map(os.path.isabs, tzpaths)):
                raise ValueError(_get_invalid_paths_message(tzpaths))
            base_tzpath = tzpaths
        else:
            env_var = os.environ.get("PYTHONTZPATH", None)
            if env_var is not None:
                base_tzpath = _parse_python_tzpath(env_var, stacklevel)
            elif sys.platform != "win32":
                base_tzpath = (
                    "/usr/share/zoneinfo",
                    "/usr/lib/zoneinfo",
                    "/usr/share/lib/zoneinfo",
                    "/etc/zoneinfo",
                )
            else:
                base_tzpath = ()

        TZPATH = tuple(base_tzpath)
        if TZPATH_CALLBACKS:
            for callback in TZPATH_CALLBACKS:
                callback(TZPATH)

    def reset_tzpath(to=None):
        # As in CPython, the warning about PYTHONTZPATH is raised from a
        # helper that is used both at import time and by this function, so
        # that each can pass the stacklevel that points at its caller.
        _reset_tzpath(to)

    TZPATH = ()
    TZPATH_CALLBACKS = []

    _reset_tzpath(stacklevel=5)
