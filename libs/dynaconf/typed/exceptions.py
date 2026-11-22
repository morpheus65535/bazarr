from dynaconf.validator import ValidationError


class DynaconfSchemaError(Exception): ...


__all__ = ["DynaconfSchemaError", "ValidationError"]
