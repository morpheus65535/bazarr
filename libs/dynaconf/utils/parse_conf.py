from __future__ import annotations

import json
import os
import re
import string
import warnings
from contextlib import suppress
from functools import wraps

from dynaconf.nodes import DataDict
from dynaconf.nodes import recursively_evaluate_lazy_format
from dynaconf.utils import extract_json_objects
from dynaconf.utils import isnamedtupleinstance
from dynaconf.utils import multi_replace
from dynaconf.utils.functional import empty
from dynaconf.vendor import toml
from dynaconf.vendor import tomllib

try:
    import jinja2
    from jinja2.sandbox import SandboxedEnvironment

    jinja_env = SandboxedEnvironment()
    for p_method in ("abspath", "realpath", "relpath", "dirname", "basename"):
        jinja_env.filters[p_method] = getattr(os.path, p_method)
except ImportError:  # pragma: no cover
    jinja_env = None

true_values = ("t", "true", "enabled", "1", "on", "yes")
false_values = ("f", "false", "disabled", "0", "off", "no", "")


KV_PATTERN = re.compile(r"([a-zA-Z0-9_.  ]*=[a-zA-Z0-9_.\-:/@]*)")
"""matches `a=b, c=d, e=f` used on `VALUE='@merge foo=bar'` variables."""

KV_PATTERN_QUOTED = re.compile(
    r"""([a-zA-Z0-9_.]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([a-zA-Z0-9_.\-:/@]*))"""
)
"""
Matches key=value pairs with optional quoted values.
Supports: key=value, key="value with spaces", key='value with, comma'
Captures: (key, double_quoted_val, single_quoted_val, unquoted_val)
"""


class DynaconfFormatError(Exception):
    """Error to raise when formatting a lazy variable fails"""


class DynaconfParseError(Exception):
    """Error to raise when parsing @casts"""


class DynaconfFileNotFoundError(FileNotFoundError):
    """Error to raise when a file is not found"""


def _parse_quoted_string(value: str) -> tuple[str, str]:
    """
    Parse a string that may contain quoted values.

    Returns (unquoted_value, remainder)

    Examples:
        '"quoted value" rest' -> ("quoted value", "rest")
        "'quoted' rest" -> ("quoted", "rest")
        'unquoted rest' -> ("unquoted", "rest")
    """
    value = value.strip()

    if not value:
        return "", ""

    # Check for quotes at start
    if value[0] in ('"', "'"):
        quote = value[0]
        try:
            end_idx = value.index(quote, 1)
            return value[1:end_idx], value[end_idx + 1 :].strip()
        except ValueError:
            # Unclosed quote - treat as error
            raise DynaconfFormatError(f"Unclosed quote in: {value}")
    else:
        # Not quoted - split on whitespace
        parts = value.split(maxsplit=1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]


class MetaValue:
    """A Marker to trigger specific actions on `set` and `object_merge`"""

    _meta_value = True

    def __init__(self, value, box_settings):
        self.box_settings = box_settings
        self.value = parse_conf_data(
            value, tomlfy=True, box_settings=box_settings
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value}) on {id(self)}"

    def unwrap(self):
        return self.value


class Reset(MetaValue):
    """Triggers an existing key to be reset to its value
    NOTE: DEPRECATED on v3.0.0
    """

    _dynaconf_reset = True

    def __init__(self, value, box_settings):
        self.box_settings = box_settings
        self.value = parse_conf_data(
            value, tomlfy=True, box_settings=self.box_settings
        )
        warnings.warn(f"{self.value} does not need `@reset` anymore.")


class Del(MetaValue):
    """Triggers an existing key to be deleted"""

    _dynaconf_del = True

    def unwrap(self):
        raise ValueError("Del object has no value")


class Merge(MetaValue):
    """Triggers an existing key to be merged"""

    _dynaconf_merge = True

    def __init__(self, value, box_settings, unique=False):
        if unique:
            self._dynaconf_merge_unique = True

        self.box_settings = box_settings

        self.value = parse_conf_data(
            value, tomlfy=True, box_settings=box_settings
        )

        if isinstance(self.value, (int, float, bool)):
            # @merge 1, @merge 1.1, @merge False
            self.value = [self.value]
        elif isinstance(self.value, str):
            # @merge {"valid": "json"}
            json_object = list(
                extract_json_objects(
                    multi_replace(
                        self.value,
                        {
                            ": True": ": true",
                            ":True": ": true",
                            ": False": ": false",
                            ":False": ": false",
                            ": None": ": null",
                            ":None": ": null",
                        },
                    )
                )
            )
            if len(json_object) == 1:
                self.value = json_object[0]
            else:
                # Try quoted pattern first (supports key="value" and key='value')
                matches = KV_PATTERN_QUOTED.findall(self.value)
                if matches:
                    # matches is list of tuples: (key, double_quoted, single_quoted, unquoted)
                    self.value = {}
                    for match in matches:
                        key = match[0].strip()
                        # Value is in one of: match[1] (double quoted), match[2] (single quoted), match[3] (unquoted)
                        value = match[1] or match[2] or match[3]
                        self.value[key] = parse_conf_data(
                            value, tomlfy=True, box_settings=box_settings
                        )
                else:
                    # Fallback to old pattern for backward compatibility
                    matches = KV_PATTERN.findall(self.value)
                    # a=b, c=d
                    if matches:
                        self.value = {
                            k.strip(): parse_conf_data(
                                v, tomlfy=True, box_settings=box_settings
                            )
                            for k, v in (
                                match.strip().split("=") for match in matches
                            )
                        }
                    elif "," in self.value:
                        # @merge foo,bar
                        self.value = [
                            parse_conf_data(
                                v, tomlfy=True, box_settings=box_settings
                            )
                            for v in self.value.split(",")
                        ]
                    else:
                        # @merge foo
                        self.value = [self.value]

        self.unique = unique


class Insert(MetaValue):
    """Triggers the value to be inserted into a list at specific index"""

    _dynaconf_insert = True

    def __init__(self, value, box_settings):
        """
        Parse value which can be in formats:
        - `0 foo` or `-1 foo` - index and value
        - `0 "foo bar"` - index and quoted multi-word value
        - `foo` - value only (index defaults to 0)
        - `"foo bar"` - quoted value only (index defaults to 0)
        - `42 foo` - number as index with value
        - `42` - just a value (treated as value, not index)

        Supports quoted values with single or double quotes for multi-word values.

        Examples:
            -1 foo -> index = -1, value = "foo"
            0 "foo bar" -> index = 0, value = "foo bar"
            'hello world' -> index = 0, value = "hello world"
            42 "value" -> index = 42, value = "value"
            @json {"key": "value"} -> index = 0, value = {"key": "value"}
        """
        self.box_settings = box_settings

        # Parse first token (might be index or value, might be quoted)
        first_token, remainder = _parse_quoted_string(value)

        # Determine if first token is an index (number)
        try:
            # Check if first token looks like a number (including negative)
            if first_token and first_token.lstrip("-+")[0].isdigit():
                # First token is a number, treat as index
                index = int(first_token)
                # The remainder is the value (might be quoted or contain @converters)
                if remainder:
                    # If remainder starts with a quote, parse it as quoted string
                    # Otherwise, use the whole remainder as-is (may contain @converters)
                    if remainder and remainder[0] in ('"', "'"):
                        parsed_value, _ = _parse_quoted_string(remainder)
                    else:
                        parsed_value = remainder
                else:
                    # No value provided, treat first token as value instead
                    index = 0
                    parsed_value = first_token
            else:
                # First token is not a number, it's the value
                # If there's a remainder, combine them (e.g., "@json {data}")
                if remainder:
                    parsed_value = value  # Use original value
                else:
                    parsed_value = first_token
                index = 0
        except (ValueError, IndexError):
            # Not a valid number or empty, treat as value with index 0
            index = 0
            parsed_value = value  # Use original value

        self.index = index
        self.value = parse_conf_data(
            parsed_value, tomlfy=True, box_settings=box_settings
        )


class BaseFormatter:
    def __init__(self, function, token):
        self.function = function
        self.token = token

    def __call__(self, value, **context):
        try:
            return self.function(value, **context)
        except (KeyError, AttributeError) as exc:
            # A template like `{this.KEY}` failed with AttributeError
            # Or KeyError in the case of `{env[KEY]}`
            raise DynaconfFormatError(
                f"Dynaconf can't interpolate variable because {exc}"
            ) from exc

    def __str__(self):
        return str(self.token)


def _jinja_formatter(value: str, **context) -> str:
    if jinja_env is None:  # pragma: no cover
        raise ImportError(
            "jinja2 must be installed to enable '@jinja' settings in dynaconf"
        )
    try:
        return jinja_env.from_string(value).render(**context)
    except jinja2.exceptions.SecurityError:
        warnings.warn(f"Unsafe access attempt to: {value}")
        return ""


def _get_formatter(value, **context):
    """
    Invokes settings.get from the annotation in value.

    value can be one of the following:

    @get KEY
    @get KEY @int
    @get KEY default_value
    @get KEY @int default_value
    @get KEY "default value"
    @get KEY @int "default value"
    @get KEY "default value" @int

    @marker KEY_TO_LOOKUP @OPTIONAL_CAST OPTIONAL_DEFAULT_VALUE

    key group will match the key
    cast group will match anything provided after @
    the default group will match single-word or quoted multi-word values
    """
    tokens = value.strip().split()
    if not tokens:
        raise DynaconfFormatError(f"Error parsing {value}: no key specified")

    key = tokens[0]
    cast = None
    default = None
    remainder = " ".join(tokens[1:])

    while remainder:
        remainder = remainder.strip()
        if not remainder:
            break

        if remainder[0] in ('"', "'"):
            # Quoted value (default)
            parsed, remainder = _parse_quoted_string(remainder)
            default = parsed
        elif remainder.startswith("@"):
            # Cast token
            parts = remainder.split(maxsplit=1)
            cast = parts[0]
            remainder = parts[1] if len(parts) > 1 else ""
        else:
            # Unquoted default (single word)
            parts = remainder.split(maxsplit=1)
            default = parts[0]
            remainder = parts[1] if len(parts) > 1 else ""

    params = {"key": key}
    if default is not None:
        params["default"] = default
    if cast:
        params["cast"] = cast

    if default is None and key not in context["this"]:
        raise DynaconfParseError(
            f"Key {key} not found in settings and no default value provided."
        )

    return context["this"].get(**params)


def _read_file_formatter(value, **context):
    """Reads a file and returns its content.
    takes a file path, reads the content and returns it.

    @read_file /abspath/path/to/file
    @read_file relative/path/to/file
    @read_file file
    @read_file file default_value
    @read_file "/path/with spaces/file.txt"
    @read_file "/path/file.txt" default_value

    @marker FILEPATH OPTIONAL_DEFAULT_VALUE

    The path can be absolute or relative to the current working directory,
    default_value can be set to return if the file does not exist.
    Paths with spaces must be quoted (single or double quotes).
    Raises error if file cannot be read.
    Sets empty string if file is empty.
    Only UTF-8 encoded text files are supported.

    Can be composed with @get, @jinja and @format

    @read_file @jinja /path/to/{{this.FILENAME}}
    @read_file @format /path/to/{this.FILENAME}
    @read_file @get FILENAME
    """
    if isinstance(value, Lazy):
        value = value(context["this"], context["env"])

    value = value.strip()
    if not value:
        raise DynaconfFormatError("Error parsing: no path specified")

    # Parse path (may be quoted)
    path, remainder = _parse_quoted_string(value)
    default = remainder.strip() if remainder else None

    # Validate path is not empty after parsing
    if not path:
        raise DynaconfFormatError("Error parsing: empty path")

    # Check if path exists and is a file
    if os.path.exists(path):
        if not os.path.isfile(path):
            raise DynaconfFormatError(f"{path} is not a file")

        try:
            with open(path, encoding="utf-8") as file:
                return file.read()
        except PermissionError:
            raise DynaconfFormatError(f"Permission denied reading {path}")
        except UnicodeDecodeError:
            raise DynaconfFormatError(
                f"{path} is not a UTF-8 text file (binary files not supported)"
            )
        except OSError as e:
            # Covers other I/O errors (file locked, disk full, etc.)
            raise DynaconfFormatError(f"Error reading {path}: {e}")
    elif default is not None:
        return default
    else:
        raise DynaconfFileNotFoundError(
            f"File {path} does not exist and no default value provided."
        )


class SafeFormatter(string.Formatter):
    def get_field(self, field_name, args, context):
        self._validate_key_exists(field_name, context)
        return super().get_field(field_name, args, context)

    def _validate_key_exists(self, field_name: str, context):
        if not field_name.lower().startswith("this"):
            return
        from dynaconf.base import _PUBLIC_PROPERTIES

        field_name = field_name.replace("[", ".")
        field_name = field_name.replace("]", "")
        context_name, _, key = field_name.partition(".")
        # these are accessible by the user, but are not considered setting keys
        # e.g, settings.current_env
        if key in _PUBLIC_PROPERTIES:
            return
        # allow only existing setting keys
        if key not in context[context_name]:
            raise AttributeError(key)


def _format_formatter(input: str, **context) -> str:
    return SafeFormatter().format(input, **context)


class Formatters:
    """Dynaconf builtin formatters"""

    python_formatter = BaseFormatter(_format_formatter, "format")
    jinja_formatter = BaseFormatter(_jinja_formatter, "jinja")
    get_formatter = BaseFormatter(_get_formatter, "get")
    read_file_formatter = BaseFormatter(_read_file_formatter, "read_file")


class Lazy:
    """Holds data to format lazily."""

    _dynaconf_lazy_format = True

    def __init__(
        self, value=empty, formatter=Formatters.python_formatter, casting=None
    ):
        self.value = value
        self.casting = casting
        # Sometimes a simple function is passed to the formatter.
        # but on evaluation-time, we may need to access `formatter.token`
        # so we are wrapping the fn to comply with this interface.
        if isinstance(formatter, BaseFormatter):
            self.formatter = formatter
        else:
            self.formatter = BaseFormatter(formatter, "lambda")

    @property
    def context(self):
        """Builds a context for formatting."""
        return {"env": os.environ, "this": self.settings}

    def __call__(self, settings, validator_object=None):
        """LazyValue triggers format lazily."""
        self.settings = settings
        self.context["_validator_object"] = validator_object
        result = self.formatter(self.value, **self.context)
        if self.casting is not None:
            result = self.casting(result)
        return result

    def __str__(self):
        """Gives string representation for the object."""
        return str(self.value)

    def __repr__(self):
        """Give the quoted str representation"""
        return f"'@{self.formatter} {self.value}'"

    def _dynaconf_encode(self):
        """Encodes this object values to be serializable to json"""
        return f"@{self.formatter} {self.value}"

    def set_casting(self, casting):
        """Set the casting and return the instance."""
        self.casting = casting
        return self


def try_to_encode(value, callback=str):
    """Tries to encode a value by verifying existence of `_dynaconf_encode`"""
    try:
        return value._dynaconf_encode()
    except (AttributeError, TypeError):
        return callback(value)


def evaluate_lazy_format(f):
    """Marks a method on Settings instance to
    lazily evaluate LazyFormat objects upon access."""

    @wraps(f)
    def evaluate(settings, *args, **kwargs):
        value = f(settings, *args, **kwargs)
        return recursively_evaluate_lazy_format(value, settings)

    return evaluate


def _safe_int_casting(value):
    """Safely cast to int with better error messages."""
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        raise DynaconfParseError(
            f"Cannot convert '{value}' to integer: {e}"
        ) from e


def _safe_float_casting(value):
    """Safely cast to float with better error messages."""
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise DynaconfParseError(
            f"Cannot convert '{value}' to float: {e}"
        ) from e


def lazy_casting(value, cast_func):
    """Helper function to handle Lazy casting."""
    return (
        value.set_casting(cast_func)
        if isinstance(value, Lazy)
        else cast_func(value)
    )


def _safe_json_parse(value):
    """Safely parse JSON, handling single quotes and Python dict syntax.

    Tries in order:
    1. Standard JSON (double quotes)
    2. Extract JSON from string with boolean/None fixes
    3. Python literal syntax (ast.literal_eval)

    This handles cases like:
    - {'key': 'value'} (Python dict syntax)
    - {"key": "It's working"} (apostrophes in values)
    - {'message': "Hello, World!"} (mixed quotes)
    """
    # First try as-is (standard JSON with double quotes)
    with suppress(json.JSONDecodeError, TypeError):
        return json.loads(value)

    # Try extracting JSON objects with boolean/None normalization
    # This handles single-quoted JSON and Python-style booleans
    with suppress(json.JSONDecodeError, ValueError, TypeError):
        json_objects = list(
            extract_json_objects(
                multi_replace(
                    value,
                    {
                        ": True": ": true",
                        ":True": ": true",
                        ": False": ": false",
                        ":False": ": false",
                        ": None": ": null",
                        ":None": ": null",
                    },
                )
            )
        )
        if json_objects:
            return json_objects[0]

    # Last resort: try ast.literal_eval for Python dict/list syntax
    import ast

    with suppress(ValueError, SyntaxError):
        return ast.literal_eval(value)

    # If all methods fail, raise clear error
    raise DynaconfParseError(f"Cannot parse as JSON: {value}")


def json_casting(value):
    """Helper function to handle JSON casting."""
    return (
        value.set_casting(_safe_json_parse)
        if isinstance(value, Lazy)
        else _safe_json_parse(value)
    )


def bool_casting(value):
    """Helper function to handle boolean casting."""
    return (
        value.set_casting(lambda x: str(x).strip().lower() in true_values)
        if isinstance(value, Lazy)
        else str(value).strip().lower() in true_values
    )


def string_casting(value, str_func):
    """Helper function to handle string transformations."""
    return (
        value.set_casting(str_func)
        if isinstance(value, Lazy)
        else str_func(str(value))
    )


converters = {
    "@str": lambda value: lazy_casting(value, str),
    "@int": lambda value: lazy_casting(value, _safe_int_casting),
    "@float": lambda value: lazy_casting(value, _safe_float_casting),
    "@bool": bool_casting,
    "@json": json_casting,
    "@format": lambda value: Lazy(value),
    "@jinja": lambda value: Lazy(value, formatter=Formatters.jinja_formatter),
    # Meta Values to trigger pre-assignment actions
    "@reset": Reset,  # @reset is DEPRECATED on v3.0.0
    "@del": Del,
    "@merge": Merge,
    "@merge_unique": lambda value, box_settings: Merge(
        value, box_settings, unique=True
    ),
    "@insert": Insert,
    "@get": lambda value: Lazy(value, formatter=Formatters.get_formatter),
    "@read_file": lambda value: Lazy(
        value, formatter=Formatters.read_file_formatter
    ),
    # String utilities
    "@upper": lambda value: string_casting(value, str.upper),
    "@lower": lambda value: string_casting(value, str.lower),
    "@title": lambda value: string_casting(value, str.title),
    "@capitalize": lambda value: string_casting(value, str.capitalize),
    "@strip": lambda value: string_casting(value, str.strip),
    "@lstrip": lambda value: string_casting(value, str.lstrip),
    "@rstrip": lambda value: string_casting(value, str.rstrip),
    "@split": lambda value: string_casting(value, str.split),
    "@casefold": lambda value: string_casting(value, str.casefold),
    "@swapcase": lambda value: string_casting(value, str.swapcase),
    # Special markers to be used as placeholders e.g., in prefilled forms
    # will always return None when evaluated
    "@note": lambda value: None,
    "@comment": lambda value: None,
    "@null": lambda value: None,
    "@none": lambda value: None,
    "@empty": lambda value: empty,
}


def apply_converter(converter_key, value, box_settings):
    """
    Get converter and apply it to @value.

    Lazy converters will return Lazy objects for later evaluation.
    """
    converter = converters[converter_key]
    try:
        converted_value = converter(value, box_settings=box_settings)
    except TypeError:
        converted_value = converter(value)
    return converted_value


def add_converter(converter_key, func):
    """Adds a new converter to the converters dict"""
    if not converter_key.startswith("@"):
        converter_key = f"@{converter_key}"

    converters[converter_key] = wraps(func)(
        lambda value: value.set_casting(func)
        if isinstance(value, Lazy)
        else Lazy(
            value,
            casting=func,
            formatter=BaseFormatter(lambda x, **_: x, converter_key),
        )
    )


def parse_with_toml(data):
    """Uses TOML syntax to parse data"""
    try:  # try tomllib first
        try:
            return tomllib.loads(f"key={data}")["key"]
        except (tomllib.TOMLDecodeError, KeyError):
            return data
    except UnicodeDecodeError:  # pragma: no cover
        # fallback to toml (TBR in 4.0.0)
        try:
            return toml.loads(f"key={data}")["key"]
        except (toml.TomlDecodeError, KeyError):
            return data
        warnings.warn(
            "TOML files should have only UTF-8 encoded characters. "
            "starting on 4.0.0 dynaconf will stop allowing invalid chars.",
            DeprecationWarning,
        )


def _parse_conf_data(data, tomlfy=False, box_settings=None):
    """
    @int @bool @float @json (for lists and dicts)
    strings does not need converters

    export DYNACONF_DEFAULT_THEME='material'
    export DYNACONF_DEBUG='@bool True'
    export DYNACONF_DEBUG_TOOLBAR_ENABLED='@bool False'
    export DYNACONF_PAGINATION_PER_PAGE='@int 20'
    export DYNACONF_MONGODB_SETTINGS='@json {"DB": "quokka_db"}'
    export DYNACONF_ALLOWED_EXTENSIONS='@json ["jpg", "png"]'
    """
    # not enforced to not break backwards compatibility with custom loaders
    box_settings = box_settings or {}

    castenabled = box_settings.get("AUTO_CAST_FOR_DYNACONF", empty)
    if castenabled is empty:
        castenabled = (
            os.environ.get("AUTO_CAST_FOR_DYNACONF", "true").lower()
            not in false_values
        )

    if (
        castenabled
        and data
        and isinstance(data, str)
        and data.partition(" ")[0] in converters
    ):
        # Check combination token is used
        comb_token = re.match(
            f"^({'|'.join(converters.keys())}) @(jinja|format|read_file|get)",
            data,
        )
        if comb_token:
            tokens = comb_token.group(0)
            converter_key_list = tokens.split(" ")
            value = data.replace(tokens, "").strip()
        else:
            parts = data.partition(" ")
            converter_key_list = [parts[0]]
            value = parts[-1]

        # Parse the converters iteratively
        for converter_key in converter_key_list[::-1]:
            value = apply_converter(converter_key, value, box_settings)
    else:
        value = parse_with_toml(data) if tomlfy else data

    if isinstance(value, dict) and box_settings.get("DYNABOXIFY", True):
        value = DataDict(value, box_settings=box_settings)

    return value


def parse_conf_data(data, tomlfy=False, box_settings=None, tomlfy_filter=None):
    """
    Apply parsing tokens recursively and return transformed data.

    Strings with lazy parser (e.g, @format) will become Lazy objects.
    """

    def in_tomlfy_filter(key):
        if not tomlfy_filter:
            return False
        for k in tomlfy_filter:
            if isinstance(k, str):  # dotted-path aware comparison for str
                _, _, k_leaf = k.partition(".")
                if key.lower() == k_leaf.lower():
                    return True
            elif k == key:  # it may no be a string, so just compare
                return True
        return False

    # fix for https://github.com/dynaconf/dynaconf/issues/595
    if isnamedtupleinstance(data):
        return data

    # not enforced to not break backwards compatibility with custom loaders
    box_settings = box_settings or {}

    if isinstance(data, (tuple, list)):
        # recursively parse each sequence item
        return [
            parse_conf_data(
                item,
                tomlfy=tomlfy,
                box_settings=box_settings,
                tomlfy_filter=tomlfy_filter,
            )
            for item in data
        ]

    if isinstance(data, DataDict):
        # recursively parse inner dict items
        # It is important to keep the same object id because
        # of mutability
        for k, v in data.items(bypass_eval=True):
            data[k] = parse_conf_data(
                v,
                tomlfy=tomlfy,
                box_settings=box_settings,
                tomlfy_filter=tomlfy_filter,
            )
        return data

    if isinstance(data, dict):
        # recursively parse inner dict items
        # It is important to keep the same object id because
        # of mutability
        for k, v in data.items():
            should_tomlfy = tomlfy and in_tomlfy_filter(k)
            data[k] = parse_conf_data(
                v,
                tomlfy=should_tomlfy,
                box_settings=box_settings,
                tomlfy_filter=tomlfy_filter,
            )
        return data

    # return parsed string value
    return _parse_conf_data(data, tomlfy=tomlfy, box_settings=box_settings)


def unparse_conf_data(value):
    if isinstance(value, bool):
        return f"@bool {value}"

    if isinstance(value, int):
        return f"@int {value}"

    if isinstance(value, float):
        return f"@float {value}"

    if isinstance(value, (list, dict)):
        return f"@json {json.dumps(value)}"

    if isinstance(value, Lazy):
        return try_to_encode(value)

    if value is None:
        return "@none "

    return value


def boolean_fix(value: str | None):
    """Gets a value like `True/False` and turns to `true/false`
    This function exists because of issue #976
    Toml parser casts booleans from true/false lower case
    however envvars are usually exported as True/False capitalized
    by mistake, this helper fixes it for envvars only.

    Assume envvars are always str.
    """
    if value and value.strip() in ("True", "False"):
        return value.lower()
    return value
