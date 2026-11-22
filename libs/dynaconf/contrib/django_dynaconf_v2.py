"""Dynaconf django extension

In the `django_project/settings.py` put at the very bottom of the file:

# HERE STARTS DYNACONF EXTENSION LOAD (Keep at the very bottom of settings.py)
# Read more at https://www.dynaconf.com/django/
import dynaconf  # noqa
settings = dynaconf.DjangoDynaconf(__name__)  # noqa
# HERE ENDS DYNACONF EXTENSION LOAD (No more code below this line)

Now in the root of your Django project
(the same folder where manage.py is located)

Put your config files `settings.{py|yaml|toml|ini|json}`
and or `.secrets.{py|yaml|toml|ini|json}`

On your projects root folder now you can start as::

    DJANGO_DEBUG='false' \
    DJANGO_ALLOWED_HOSTS='["localhost"]' \
    python manage.py runserver
"""

from __future__ import annotations

import inspect
import os
import sys

import dynaconf
from dynaconf.hooking import Action
from dynaconf.hooking import Hook
from dynaconf.hooking import HookableSettings

try:  # pragma: no cover
    from django import conf
    from django.conf import settings as django_settings

    django_installed = True
except ImportError:  # pragma: no cover
    django_installed = False


# Compat with Django 5.x
def _add_script_prefix(value):  # pragma: nocover
    """
    Add SCRIPT_NAME prefix to relative paths.

    Useful when the app is being served at a subpath and manually prefixing
    subpath to STATIC_URL and MEDIA_URL in settings is inconvenient.
    """
    # Don't apply prefix to absolute paths and URLs.
    if value.startswith(("http://", "https://", "/")):
        return value
    from django.urls import get_script_prefix

    return f"{get_script_prefix()}{value}"


# Special case some settings which require further modification.
# This is done here for performance reasons so the modified value is cached.
def fix_absolute_urls(_settings):  # pragma: nocover
    data = {}
    if media_url := _settings.get("MEDIA_URL"):
        data["MEDIA_URL"] = _add_script_prefix(media_url)
    if static_url := _settings.get("STATIC_URL"):
        data["STATIC_URL"] = _add_script_prefix(static_url)
    return data


def load(django_settings_module_name=None, **kwargs):  # pragma: no cover
    converters_before_loading = set(
        dynaconf.utils.parse_conf.converters.keys()
    )
    if not django_installed:
        raise RuntimeError(
            "To use this extension django must be installed "
            "install it with: pip install django"
        )

    try:
        django_settings_module = sys.modules[django_settings_module_name]
    except KeyError:
        django_settings_module = sys.modules[
            os.environ["DJANGO_SETTINGS_MODULE"]
        ]

    settings_module_name = django_settings_module.__name__
    settings_file = os.path.abspath(django_settings_module.__file__)
    _root_path = os.path.dirname(settings_file)

    # 1) Create the lazy settings object reusing settings_module consts
    options = {
        k: v
        for k, v in inspect.getmembers(django_settings_module)
        if k.isupper()
    }
    options.update(kwargs)
    options.setdefault(
        "SKIP_FILES_FOR_DYNACONF", [settings_file, "dynaconf_merge"]
    )
    options.setdefault("ROOT_PATH_FOR_DYNACONF", _root_path)
    options.setdefault("ENVVAR_PREFIX_FOR_DYNACONF", "DJANGO")
    options.setdefault("ENV_SWITCHER_FOR_DYNACONF", "DJANGO_ENV")
    options.setdefault("ENVIRONMENTS_FOR_DYNACONF", True)
    options.setdefault("load_dotenv", True)
    options.setdefault(
        "default_settings_paths", dynaconf.DEFAULT_SETTINGS_FILES
    )
    options.setdefault("_wrapper_class", HookableSettings)

    class UserSettingsHolder(dynaconf.LazySettings):
        _django_override = True

    lazy_settings = dynaconf.LazySettings(**options)
    dynaconf.settings = lazy_settings  # rebind the settings

    # 2) Set all settings back to django_settings_module for 'django check'
    lazy_settings.populate_obj(django_settings_module)

    # 3) Bind `settings` and `DYNACONF`
    setattr(django_settings_module, "settings", lazy_settings)
    setattr(django_settings_module, "DYNACONF", lazy_settings)

    # 4) keep django original settings
    # dir(django_settings) triggers _setup() which populates _wrapped.
    # Read from _wrapped directly to bypass LazySettings.__getattr__
    # validation (e.g. empty SECRET_KEY raises ImproperlyConfigured,
    # not AttributeError, so getattr's default can't catch it).
    dj = {}
    for key in dir(django_settings):
        if (
            key.isupper()
            and (key != "SETTINGS_MODULE")
            and key not in lazy_settings.store
        ):
            wrapped = django_settings._wrapped
            val = getattr(wrapped, key, None)
            dj[key] = val
        dj["ORIGINAL_SETTINGS_MODULE"] = (
            django_settings._wrapped.SETTINGS_MODULE
        )

    lazy_settings.update(dj)

    # 2 pass execution, 1st immediately and second deferred
    # to post hooks so it can fix URLS added later in the
    # loading pipeline
    lazy_settings.update(fix_absolute_urls(lazy_settings))
    config = lazy_settings.__core__.config
    config.post_hooks.append(fix_absolute_urls)

    # Allow dynaconf_hooks to be in the same folder as the django.settings
    dynaconf.loaders.execute_hooks(
        "post",
        lazy_settings,
        lazy_settings.current_env,
        modules=[settings_module_name],
        files=[settings_file],
    )
    config.loaded_py_modules.insert(0, settings_module_name)

    # 5) Patch django.conf.settings
    class Wrapper:
        # lazy_settings = conf.settings.lazy_settings

        def __getattribute__(self, name):
            if name == "settings":
                return lazy_settings
            if name == "UserSettingsHolder":
                return UserSettingsHolder
            return getattr(conf, name)

    # This implementation is recommended by Guido Van Rossum
    # https://mail.python.org/pipermail/python-ideas/2012-May/014969.html
    sys.modules["django.conf"] = Wrapper()

    # 5b) Replay Django's LazySettings.__getattr__ validations
    # (e.g. empty SECRET_KEY raises ImproperlyConfigured).
    # django_settings._wrapped is populated from step 4's dir() call.
    _original_django_settings = django_settings

    def _django_validate_hook(temp_settings, value, *args, **kwargs):
        key = args[0] if args else kwargs.get("key")
        if key and key.isupper():
            try:
                conf.LazySettings.__getattr__(_original_django_settings, key)
            except AttributeError:
                # Key exists in dynaconf but not in Django's Settings.
                # Not a Django-managed key, so no validation to apply.
                pass
        return value

    hooks = lazy_settings.store.get("_registered_hooks", {})
    hooks.setdefault(Action.AFTER_GET, []).append(Hook(_django_validate_hook))
    lazy_settings["_registered_hooks"] = hooks

    # 6) Enable standalone scripts to use Dynaconf
    # This is for when `django.conf.settings` is imported directly
    # on external `scripts` (out of Django's lifetime)
    for stack_item in reversed(inspect.stack()):
        if isinstance(
            stack_item.frame.f_globals.get("settings"), conf.LazySettings
        ):
            stack_item.frame.f_globals["settings"] = lazy_settings

    if converters_before_loading != set(
        dynaconf.utils.parse_conf.converters.keys()
    ):
        # When new converter keys are added after settings initialization
        # it is required to reload the settings so values a re-evaluated
        # with the new converters.
        lazy_settings.reload()
    return lazy_settings


# syntax sugar
DjangoDynaconf = load  # noqa
