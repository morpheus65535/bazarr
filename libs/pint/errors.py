"""
    pint.errors
    ~~~~~~~~~~~

    Functions and classes related to unit definitions and conversions.

    :copyright: 2016 by Pint Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

OFFSET_ERROR_DOCS_HTML = "https://pint.readthedocs.io/en/latest/nonmult.html"
LOG_ERROR_DOCS_HTML = "https://pint.readthedocs.io/en/latest/nonmult.html"


def _file_prefix(filename=None, lineno=None):
    if filename and lineno is not None:
        return f"While opening {filename}, in line {lineno}: "
    elif filename:
        return f"While opening {filename}: "
    elif lineno is not None:
        return f"In line {lineno}: "
    else:
        return ""


class DefinitionSyntaxError(SyntaxError):
    """Raised when a textual definition has a syntax error."""

    def __init__(self, msg, *, filename=None, lineno=None):
        super().__init__(msg)
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        return _file_prefix(self.filename, self.lineno) + str(self.args[0])

    @property
    def __dict__(self):
        # SyntaxError.filename and lineno are special fields that don't appear in
        # the __dict__. This messes up pickling and deepcopy, as well
        # as any other Python library that expects sane behaviour.
        return {"filename": self.filename, "lineno": self.lineno}

    def __reduce__(self):
        return DefinitionSyntaxError, self.args, self.__dict__


class RedefinitionError(ValueError):
    """Raised when a unit or prefix is redefined."""

    def __init__(self, name, definition_type, *, filename=None, lineno=None):
        super().__init__(name, definition_type)
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        msg = f"Cannot redefine '{self.args[0]}' ({self.args[1]})"
        return _file_prefix(self.filename, self.lineno) + msg

    def __reduce__(self):
        return RedefinitionError, self.args, self.__dict__


class UndefinedUnitError(AttributeError):
    """Raised when the units are not defined in the unit registry."""

    def __init__(self, *unit_names):
        if len(unit_names) == 1 and not isinstance(unit_names[0], str):
            unit_names = unit_names[0]
        super().__init__(*unit_names)

    def __str__(self):
        if len(self.args) == 1:
            return f"'{self.args[0]}' is not defined in the unit registry"
        return f"{self.args} are not defined in the unit registry"


class PintTypeError(TypeError):
    pass


class DimensionalityError(PintTypeError):
    """Raised when trying to convert between incompatible units."""

    def __init__(self, units1, units2, dim1="", dim2="", *, extra_msg=""):
        super().__init__()
        self.units1 = units1
        self.units2 = units2
        self.dim1 = dim1
        self.dim2 = dim2
        self.extra_msg = extra_msg

    def __str__(self):
        if self.dim1 or self.dim2:
            dim1 = f" ({self.dim1})"
            dim2 = f" ({self.dim2})"
        else:
            dim1 = ""
            dim2 = ""

        return (
            f"Cannot convert from '{self.units1}'{dim1} to "
            f"'{self.units2}'{dim2}{self.extra_msg}"
        )

    def __reduce__(self):
        return TypeError.__new__, (DimensionalityError,), self.__dict__


class OffsetUnitCalculusError(PintTypeError):
    """Raised on ambiguous operations with offset units."""

    def __str__(self):
        return (
            "Ambiguous operation with offset unit (%s)."
            % ", ".join(str(u) for u in self.args)
            + " See "
            + OFFSET_ERROR_DOCS_HTML
            + " for guidance."
        )


class LogarithmicUnitCalculusError(PintTypeError):
    """Raised on inappropriate operations with logarithmic units."""

    def __str__(self):
        return (
            "Ambiguous operation with logarithmic unit (%s)."
            % ", ".join(str(u) for u in self.args)
            + " See "
            + LOG_ERROR_DOCS_HTML
            + " for guidance."
        )


class UnitStrippedWarning(UserWarning):
    pass
