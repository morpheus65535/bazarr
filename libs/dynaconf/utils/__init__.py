from __future__ import annotations

import json
import os
import warnings
from collections import defaultdict
from collections.abc import Iterator
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import TypeVar

from dynaconf.utils.functional import empty

if TYPE_CHECKING:  # pragma: no cover
    from dynaconf.base import LazySettings
    from dynaconf.base import Settings
    from dynaconf.nodes import DataDict
    from dynaconf.nodes import DataNode


BANNER = """
██████╗ ██╗   ██╗███╗   ██╗ █████╗  ██████╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗╚██╗ ██╔╝████╗  ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║██╔════╝
██║  ██║ ╚████╔╝ ██╔██╗ ██║███████║██║     ██║   ██║██╔██╗ ██║█████╗
██║  ██║  ╚██╔╝  ██║╚██╗██║██╔══██║██║     ██║   ██║██║╚██╗██║██╔══╝
██████╔╝   ██║   ██║ ╚████║██║  ██║╚██████╗╚██████╔╝██║ ╚████║██║
╚═════╝    ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝
"""

if os.name == "nt":  # pragma: no cover
    # windows can't handle the above charmap
    BANNER = "DYNACONF"

ListMergeOptions = Literal["merge", "shallow", "deep"]


def object_merge(
    old: Any,
    new: Any,
    unique: bool = False,
    full_path: Optional[list[str]] = None,
    list_merge: ListMergeOptions = "merge",
) -> Any:
    """
    Recursively merge two data structures, new is mutated in-place.

    :param old: The existing data.
    :param new: The new data to get old values merged in to.
    :param unique: When set to True existing list items are not set.
    :param full_path: Indicates the elements of a tree.
    :param list_merge: Methods to use to merge lists
        - merge: default merge behavior, i.e. (unique) concatenation
        - shallow: replace the top-most level list of the nested structure
        - deep: iteratively traverse the nested structure and replace
            the element in the list at the level specified by the full_path
    """
    if full_path is None:
        full_path = []
    if old == new or old is None or new is None:
        # Nothing to merge
        return new

    if isinstance(old, list) and isinstance(new, list):
        # 726: allow local_merge to override global merge on lists
        if "dynaconf_merge_unique" in new:
            new.remove("dynaconf_merge_unique")
            unique = True

        if list_merge == "merge" or unique:
            for item in old[::-1]:
                if unique and item in new:
                    continue
                new.insert(0, item)
        elif list_merge == "deep" and len(full_path) > 0:  # element-wise merge
            new.extend([[]] * max(len(old) - len(new), 0))
            for ii, item in enumerate(old):
                # replace at corresponding positions
                if list_merge == "shallow":
                    new[ii] = new[ii] or item
                else:  # deep replace
                    if not new[ii]:  # copy over the older values
                        new[ii] = item
                    elif item:  # old[ii] is not None
                        object_merge(
                            old[ii],
                            new[ii],
                            full_path=full_path[1:],
                            list_merge="deep",
                        )

    if isinstance(old, dict) and isinstance(new, dict):
        existing_value = recursive_get(old, full_path)  # doesn't handle None
        # Need to make every `None` on `_store` to be an wrapped `LazyNone`

        # data coming from source, in `new` can be mix case: KEY4|key4|Key4
        # data existing on `old` object has the correct case: key4|KEY4|Key4
        # So we need to ensure that new keys matches the existing keys
        for new_key in tuple(new.keys()):
            correct_case_key = find_the_correct_casing(
                new_key, tuple(old.keys())
            )
            if correct_case_key:
                new[correct_case_key] = new.pop(new_key)

        def safe_items(data):
            """
            Get items from DataDict without triggering recursive evaluation
            """
            if data.__class__.__name__ == "DataDict":
                return data.items(bypass_eval=True)
            else:
                return data.items()

        # local mark may set dynaconf_merge=False
        should_merge = new.pop("dynaconf_merge", True)
        if should_merge:
            for old_key, value in safe_items(old):
                # This is for when the dict exists internally
                # but the new value on the end of full path is the same
                if (
                    existing_value is not None
                    and len(full_path) == 1
                    and old_key.lower() == full_path[-1].lower()
                    and existing_value is value
                ):
                    # Here Be The Dragons
                    # This comparison needs to be smarter
                    continue

                if old_key not in new:
                    new[old_key] = value
                else:
                    new[old_key] = object_merge(
                        value,
                        new[old_key],
                        full_path=full_path[1:] if full_path else None,
                        list_merge=list_merge,
                    )

            # Restore old key order: keys that exist in old keep old's
            # relative order; keys that are new-only come last.
            old_keys = list(safe_items(old))
            old_key_set = {k for k, _ in old_keys}
            new_only = [k for k in new if k not in old_key_set]
            ordered = [k for k, _ in old_keys if k in new] + new_only
            for k in ordered:
                new[k] = new.pop(k)

        handle_metavalues(old, new, list_merge=list_merge)

    return new


def recursive_get(
    obj: DataDict | dict[str, int] | dict[str, str | int],
    names: list[str] | None,
) -> Any:
    """Given a dot accessible object and a list of names `foo.bar.[1].zaz`
    gets recursively all names one by one obj.foo.bar.[1].zaz.
    """
    if not names or obj is None:
        return
    head, *tail = names
    if "[" not in head:
        result = getattr(obj, head, None)
    elif (index_string := head[1:-1]).isdigit():  # expect "[123]"
        index = int(index_string)
        result = obj[index] if index < len(obj) else []
    else:
        result = getattr(obj, head, None)

    if not tail:
        return result

    return recursive_get(result, tail)


def _strip_merge_tokens(data: dict) -> None:
    """Remove dynaconf_merge tokens from a dict tree without merging."""
    for key in list(data.keys()):
        if isinstance(data[key], dict):
            data[key].pop("dynaconf_merge", None)
            data[key].pop("dynaconf_merge_unique", None)
            _strip_merge_tokens(data[key])


def handle_metavalues(
    old: DataDict | dict[str, int] | dict[str, str | int],
    new: Any,
    list_merge: ListMergeOptions = "merge",
) -> None:
    """
    Cleanup of MetaValues on new dict
    :param old: old values
    :param new: new values
    :param list_merge: Methods to use to merge lists
        - merge: default merge behavior, i.e. (unique) concatenation
        - shallow: replace the top-most level list of the nested structure
        - deep: iteratively traverse the nested structure and replace
            the element in the list at the level specified by the full_path
    """

    for key in list(new.keys()):
        # MetaValue instances
        if getattr(new[key], "_dynaconf_reset", False):  # pragma: no cover
            # a Reset on `new` triggers reasign of existing data
            new[key] = new[key].unwrap()
        elif getattr(new[key], "_dynaconf_del", False):
            # a Del on `new` triggers deletion of existing data
            new.pop(key, None)
            old.pop(key, None)
        elif getattr(new[key], "_dynaconf_merge", False):
            # a Merge on `new` triggers merge with existing data
            new[key] = object_merge(
                old.get(key),
                new[key].unwrap(),
                unique=new[key].unique,
            )
        elif getattr(new[key], "_dynaconf_insert", False):
            # Insert on `new` triggers insert with existing data
            # if existing is a list it inserts at specified .index
            # if existing is not a list it creates a new list with the value
            existing = old.get(key)  # keep the same reference
            if isinstance(existing, list):  # perform insert on it
                existing.insert(new[key].index, new[key].unwrap())
                new[key] = existing
            else:
                new[key] = [new[key].unwrap()]

        # Data structures containing merge tokens
        if isinstance(new.get(key), (list, tuple)):
            has_merge = "dynaconf_merge" in new[key]
            has_merge_unique = "dynaconf_merge_unique" in new[key]
            if has_merge or has_merge_unique:
                value = list(new[key])
                unique = False

                try:
                    value.remove("dynaconf_merge")
                except ValueError:
                    value.remove("dynaconf_merge_unique")
                    unique = True

                for item in (old.get(key) or [])[::-1]:
                    if unique and item in value:
                        continue
                    value.insert(0, item)

                new[key] = value

        elif isinstance(new.get(key), dict):
            local_merge = new[key].pop(
                "dynaconf_merge", new[key].pop("dynaconf_merge_unique", None)
            )
            if local_merge not in (True, False, None) and not new[key]:
                # In case `dynaconf_merge:` holds value not boolean - ref #241
                new[key] = local_merge

            if local_merge:
                new[key] = object_merge(
                    old.get(key), new[key], list_merge=list_merge
                )
            elif key not in old:
                _strip_merge_tokens(new[key])


class FakeCore:
    """
    Workaround to support DynaconfCore + DynaconfConfig in DynaconfDict.

    When/if re-writing the loaders module we should get rid of this.
    """

    def __init__(self, dynaconf_dict):  # pragma: no cover
        self.dynaconf_dict = dynaconf_dict

    def __getattr__(self, name):  # pragma: no cover
        if name == "config":
            return self
        try:
            return getattr(self.dynaconf_dict, f"_{name}")
        except AttributeError:
            return getattr(self.dynaconf_dict, name)

    def __setattr__(self, name, value):  # pragma: no cover
        underscore_name = f"_{name}"
        if name == "dynaconf_dict":
            super().__setattr__(name, value)
        elif name in self.dynaconf_dict:
            setattr(self.dynaconf_dict, name, value)
        elif underscore_name in self.dynaconf_dict:
            setattr(self.dynaconf_dict, underscore_name, value)
        else:
            # Calling this for properly raising
            setattr(self.dynaconf_dict, name, value)


# NOTE: can we get rid of this? (and consequently of FakeCore)
class DynaconfDict(dict):
    """A dict representing en empty Dynaconf object
    useful to run loaders in to a dict for testing"""

    def __init__(self, *args, **kwargs):
        self.__core__ = FakeCore(
            self
        )  # compat with DynaconfCore + DynaconfConfig
        self._loaded_envs = []
        self._loaded_hooks = defaultdict(dict)
        self._loaded_py_modules = []
        self._loaded_files = []
        self._deleted = set()
        self._store = {}
        self._env_cache = {}
        self._loaded_by_loaders = {}
        self._loaders = []
        self._defaults = {}
        self.environ = os.environ
        self.SETTINGS_MODULE = None
        self.filter_strategy = kwargs.get("filter_strategy", None)
        self._not_installed_warnings = []
        self._validate_only = kwargs.pop("validate_only", None)
        self._validate_exclude = kwargs.pop("validate_exclude", None)
        super().__init__(*args, **kwargs)

    def set(self, key: str, value: str, *args, **kwargs) -> None:
        self[key] = value

    @staticmethod
    def get_environ(key, default=None):  # pragma: no cover
        return os.environ.get(key, default)

    def exists(self, key: str, **kwargs) -> bool:
        return self.get(key, missing) is not missing


RENAMED_VARS = {
    # old: new
    "DYNACONF_NAMESPACE": "ENV_FOR_DYNACONF",
    "NAMESPACE_FOR_DYNACONF": "ENV_FOR_DYNACONF",
    "DYNACONF_SETTINGS_MODULE": "SETTINGS_FILE_FOR_DYNACONF",
    "DYNACONF_SETTINGS": "SETTINGS_FILE_FOR_DYNACONF",
    "SETTINGS_MODULE": "SETTINGS_FILE_FOR_DYNACONF",
    "SETTINGS_MODULE_FOR_DYNACONF": "SETTINGS_FILE_FOR_DYNACONF",
    "PROJECT_ROOT": "ROOT_PATH_FOR_DYNACONF",
    "PROJECT_ROOT_FOR_DYNACONF": "ROOT_PATH_FOR_DYNACONF",
    "DYNACONF_SILENT_ERRORS": "SILENT_ERRORS_FOR_DYNACONF",
    "DYNACONF_ALWAYS_FRESH_VARS": "FRESH_VARS_FOR_DYNACONF",
    "BASE_NAMESPACE_FOR_DYNACONF": "DEFAULT_ENV_FOR_DYNACONF",
    "GLOBAL_ENV_FOR_DYNACONF": "ENVVAR_PREFIX_FOR_DYNACONF",
}

MISSPELL_OPTIONS = {
    "settings_files": "settings_file",
    "SETTINGS_FILES": "SETTINGS_FILE",
    "environment": "environments",
    "ENVIRONMENT": "ENVIRONMENTS",
}


def normalize_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Resolve names in the user provided keyword arguments."""
    from dynaconf.base import UPPER_DEFAULT_SETTINGS  # avoid circular import

    for_dynaconf_keys = {
        key for key in UPPER_DEFAULT_SETTINGS if key.endswith("_FOR_DYNACONF")
    }

    # Fix config name misspells. E.g:
    # "settings_files" -> "settings_file"
    for misspell, correct in MISSPELL_OPTIONS.items():
        if misspell in kwargs:
            kwargs[correct] = kwargs.pop(misspell)

    # Replace `_FOR_DYNACONF` aliases. E.g:
    # "root_PATH" -> "ROOT_PATH_FOR_DYNACONF"
    for key in tuple(kwargs.keys()):
        normalized_key = f"{key.upper()}_FOR_DYNACONF"
        if normalized_key in for_dynaconf_keys:
            kwargs[normalized_key] = kwargs.pop(key)

    # Keep backwards compatibility with renamed options. E.g:
    # "DYNACONF_NAMESPACE" -> "ENV_FOR_DYNACONF"
    warn_deprecations(kwargs)
    for old, new in RENAMED_VARS.items():
        if old in kwargs:
            kwargs[new] = kwargs[old]
            # update cross references
            for c_old, c_new in RENAMED_VARS.items():
                if c_new == new:
                    kwargs[c_old] = kwargs[new]

    # A list passed as `env` is the programmatic equivalent of the
    # comma-separated ENV_FOR_DYNACONF environment variable. Normalize it here
    # so all loaders can use their existing multi-environment handling. #1278
    env = kwargs.get("ENV_FOR_DYNACONF")
    if isinstance(env, list):
        if not all(isinstance(item, str) for item in env):
            raise TypeError("'env' must be a string or a list of strings")
        kwargs["ENV_FOR_DYNACONF"] = ",".join(env)
    elif env is not None and not isinstance(env, str):
        raise TypeError("'env' must be a string or a list of strings")

    return kwargs


class Missing:
    """
    Sentinel value object/singleton used to differentiate between ambiguous
    situations where `None` is a valid value.
    """

    def __bool__(self) -> bool:
        """Respond to boolean duck-typing."""
        return False

    def __eq__(self, other: DataDict | Missing) -> bool:
        """Equality check for a singleton."""

        return isinstance(other, self.__class__)

    # Ensure compatibility with Python 2.x
    __nonzero__ = __bool__

    def __repr__(self) -> str:
        """
        Unambiguously identify this string-based representation of Missing,
        used as a singleton.
        """
        return "<dynaconf.missing>"


missing = Missing()


def deduplicate(list_object: list[str]) -> list[str]:
    """Rebuild `list_object` removing duplicated and keeping order"""
    new = []
    for item in list_object:
        if item not in new:
            new.append(item)
    return new


def warn_deprecations(data: Any) -> None:
    for old, new in RENAMED_VARS.items():
        if old in data:
            warnings.warn(
                f"You are using {old} which is a deprecated settings "
                f"replace it with {new}",
                DeprecationWarning,
            )


def trimmed_split(
    s: str, seps: str | tuple[str, str] = (";", ",")
) -> list[str]:
    """Given a string s, split is by one of the seps."""
    for sep in seps:
        if sep not in s:
            continue
        data = [item.strip() for item in s.strip().split(sep)]
        return data
    return [s]  # raw un-split


T = TypeVar("T")


def ensure_a_list(data: T | list[T]) -> list[T]:
    """Ensure data is a list or wrap it in a list"""
    if not data:
        return []
    if isinstance(data, (list, tuple, set)):
        return list(data)
    if isinstance(data, str):
        data = trimmed_split(data)  # settings.toml,other.yaml
        return data
    return [data]


def ensure_upperfied_list(sequence: Sequence) -> list:
    """Ensure list of strings contains upperfied items."""
    return [
        upperfy(item) if isinstance(item, str) else item for item in sequence
    ]


def build_env_list(obj: Settings | LazySettings, env: str | None) -> list[str]:
    """Build env list for loaders to iterate.

    Arguments:
        obj {LazySettings} -- A Dynaconf settings instance
        env {str} -- The current env to be loaded

    Returns:
        [str] -- A list of string names of the envs to load.
    """
    # add the [default] env
    env_list = [(obj.get("DEFAULT_ENV_FOR_DYNACONF") or "default").lower()]

    # compatibility with older versions that still uses [dynaconf] as
    # [default] env
    global_env = (obj.get("ENVVAR_PREFIX_FOR_DYNACONF") or "dynaconf").lower()
    if global_env not in env_list:
        env_list.append(global_env)

    # add the current env counting on the case where it is a comma separated list
    current_env = obj.current_env
    if current_env and isinstance(current_env, str):
        for item in current_env.split(","):
            if item and (_name := item.strip().lower()) not in env_list:
                env_list.append(_name)

    # add a manually set env counting on the case where it is a comma separated list
    if env and isinstance(env, str):
        for item in env.split(","):
            if item and (_name := item.strip().lower()) not in env_list:
                env_list.append(_name)

    # add the [global] env
    env_list.append("global")

    return env_list


@lru_cache
def upperfy(key: str) -> str:
    """Receive a string key and returns its upper version.

    Example:

      input: foo
      output: FOO

      input: foo_bar
      output: FOO_BAR

      input: foo__bar__ZAZ
      output: FOO__bar__ZAZ

    Arguments:
        key {str} -- A string key that may contain dunders `__`

    Returns:
        The key as upper case but keeping the nested elements.
    """
    key = str(key)
    if "__" in key:
        parts = key.split("__")
        return "__".join([parts[0].upper()] + parts[1:])
    return key.upper()


def multi_replace(text: str, patterns: dict[str, str]) -> str:
    """Replaces multiple pairs in a string

    Arguments:
        text {str} -- A "string text"
        patterns {dict} -- A dict of {"old text": "new text"}

    Returns:
        text -- str
    """
    for old, new in patterns.items():
        text = text.replace(old, new)
    return text


def extract_json_objects(
    text: str, decoder=json.JSONDecoder()
) -> Iterator[dict[str, int | dict[Any, Any]]]:
    """Find JSON objects in text, and yield the decoded JSON data

    Does not attempt to look for JSON arrays, text, or other JSON types outside
    of a parent JSON object.

    """
    pos = 0
    while True:
        match = text.find("{", pos)
        if match == -1:
            break
        try:
            result, index = decoder.raw_decode(text[match:])
            yield result
            pos = match + index
        except ValueError:
            pos = match + 1


def isnamedtupleinstance(value):
    """Check if value is a namedtuple instance

    stackoverflow.com/questions/2166818/
    how-to-check-if-an-object-is-an-instance-of-a-namedtuple
    """

    t = type(value)
    b = t.__bases__
    if len(b) != 1 or b[0] is not tuple:
        return False
    f = getattr(t, "_fields", None)
    if not isinstance(f, tuple):
        return False
    return all(isinstance(n, str) for n in f)


@lru_cache
def find_the_correct_casing(
    key: str, data_keys: tuple[Any, ...]
) -> str | None:
    """Given a key, find the proper casing in data.

    Non-str keys in data are skipped.

    Arguments:
        key {str} -- A key to be searched in data
        data {dict} -- A dict to be searched

    Returns:
        str -- The proper casing of the key in data
    """
    if not isinstance(key, str) or key in data_keys:
        return key
    for k in data_keys:
        if not isinstance(k, str):
            continue
        if k.lower() == key.lower():
            return k
        if k.replace(" ", "_").lower() == key.lower():
            return k
    return None


def prepare_json(data: Any) -> Any:
    """Takes a data dict and transforms unserializable values to str for JSON.
    {1: PosixPath("/foo")} -> {"1": "/foo"}
    """
    unserializable_types = (Path,)
    if isinstance(data, dict):
        return_data = {}
        for key, val in data.items():
            value = str(val) if isinstance(val, unserializable_types) else val
            return_data[str(key)] = value
        return return_data
    elif isinstance(data, (list, tuple)):
        return_data = []
        for val in data:
            value = str(val) if isinstance(val, unserializable_types) else val
            return_data.append(value)
        return return_data
    return data


def to_dict(obj: Any) -> Any:
    """Recursively convert dict/list subclasses to plain Python types."""
    if isinstance(obj, dict):
        return {k: to_dict(obj[k]) for k in obj}
    elif isinstance(obj, list):
        return [to_dict(x) for x in obj]
    return obj


def container_items(container: dict | list):
    if isinstance(container, dict):
        return container.items()
    elif isinstance(container, list):
        return enumerate(container)
    else:
        raise TypeError(f"Unsupported container type: {type(container)}")


def data_print(data: DataNode, debug=False):
    """Data print utilities.

    Params:
        data: The data to be displayed.
        debug: Whether internal info should be displayed for debugging
    """

    if not debug:
        print(json.dumps(data, indent=4))  # noqa
        return

    class Node(TypedDict):
        metadata: dict
        children: list

    def walk(data):
        children = []
        for k, v in container_items(data):
            if isinstance(v, (dict, list)):
                node = Node(
                    metadata=v.__meta__.__dict__,
                    children=walk(v),
                )
                children.append({k: node})
            else:
                children.append({k: v})
        return children

    root = Node(
        metadata=data.__meta__.__dict__,
        children=walk(data),
    )
    print(json.dumps(root, indent=4))  # noqa
