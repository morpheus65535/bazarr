from __future__ import annotations

from os import environ

from dynaconf.utils import missing
from dynaconf.utils import upperfy
from dynaconf.utils.parse_conf import parse_conf_data

DOTENV_IMPORTED = False
try:
    from dynaconf.vendor.dotenv import cli as dotenv_cli

    DOTENV_IMPORTED = True
except ImportError:
    pass
except FileNotFoundError:
    pass


IDENTIFIER = "env"


def load(obj, env=None, silent=True, key=None):
    """Loads envvars with prefixes:

    `DYNACONF_` (default global) or `$(ENVVAR_PREFIX_FOR_DYNACONF)_`
    """
    global_prefix = obj.get("ENVVAR_PREFIX_FOR_DYNACONF")
    if global_prefix is False or global_prefix.upper() != "DYNACONF":
        load_from_env(obj, "DYNACONF", key, silent, IDENTIFIER + "_global")

    # Load the global env if exists and overwrite everything
    load_from_env(obj, global_prefix, key, silent, IDENTIFIER + "_global")


def load_from_env(
    obj,
    prefix=False,
    key=None,
    silent=False,
    identifier=IDENTIFIER,
    env=False,  # backwards compatibility bc renamed param
):
    if prefix is False and env is not False:
        prefix = env

    env_ = ""
    if prefix is not False:
        if not isinstance(prefix, str):
            raise TypeError("`prefix/env` must be str or False")

        prefix = prefix.upper()
        env_ = f"{prefix}_"

    # Load a single environment variable explicitly.
    if key:
        key = upperfy(key)
        value = environ.get(f"{env_}{key}")
        if value:
            try:  # obj is a Settings
                obj.set(key, value, loader_identifier=identifier, tomlfy=True)
            except AttributeError:  # obj is a dict
                obj[key] = parse_conf_data(
                    value, tomlfy=True, box_settings=obj
                )

    # Load environment variables in bulk (when matching).
    else:
        # Only known variables should be loaded from environment?
        ignore_unknown = obj.get("IGNORE_UNKNOWN_ENVVARS_FOR_DYNACONF")

        trim_len = len(env_)
        data = {
            key[trim_len:]: parse_conf_data(
                data, tomlfy=True, box_settings=obj
            )
            for key, data in environ.items()
            if key.startswith(env_)
            and not (
                # Ignore environment variables that haven't been
                # pre-defined in settings space.
                ignore_unknown
                and obj.get(key[trim_len:], default=missing) is missing
            )
        }
        # Update the settings space based on gathered data from environment.
        if data:
            filter_strategy = obj.get("FILTER_STRATEGY")
            if filter_strategy:
                data = filter_strategy(data)
            obj.update(data, loader_identifier=identifier)


def write(settings_path, settings_data, **kwargs):
    """Write data to .env file"""
    if not DOTENV_IMPORTED:
        return
    for key, value in settings_data.items():
        quote_mode = (
            isinstance(value, str)
            and (value.startswith("'") or value.startswith('"'))
        ) or isinstance(value, (list, dict))
        dotenv_cli.set_key(
            str(settings_path),
            key,
            str(value),
            quote_mode="always" if quote_mode else "none",
        )
