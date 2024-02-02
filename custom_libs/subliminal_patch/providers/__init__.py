# coding=utf-8

from __future__ import absolute_import

import functools
import importlib
import os
import logging
import subliminal
from subliminal.providers import Provider as _Provider
from subliminal.subtitle import Subtitle as _Subtitle
from subliminal_patch.extensions import provider_registry
from subliminal_patch.http import RetryingSession
from subliminal_patch.subtitle import Subtitle, guess_matches

from subzero.lib.io import get_viable_encoding
import six


logger = logging.getLogger(__name__)


class Provider(_Provider):
    hash_verifiable = False
    hearing_impaired_verifiable = False
    skip_wrong_fps = True

    def ping(self):
        """Check if the provider is alive."""
        return True


def reinitialize_on_error(exceptions: tuple, attempts=1):
    """Method decorator for Provider class. It will reinitialize the instance
    and re-run the method in case of exceptions.

    :param exceptions: tuple of expected exceptions
    :param attempts: number of attempts to call the method
    """

    def real_decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            inc = 1
            while True:
                try:
                    return method(self, *args, **kwargs)
                except exceptions as error:
                    if inc > attempts:
                        raise

                    logger.exception(error)
                    logger.debug("Reinitializing %s instance (%s attempt)", self, inc)

                    self.terminate()
                    self.initialize()

                    inc += 1

        return wrapper

    return real_decorator


# register providers
# fixme: this is bad
for name in os.listdir(os.path.dirname(__file__)):
    if name in ("__init__.py", "mixins.py", "utils.py") or not name.endswith(".py"):
        continue

    module_name = os.path.splitext(name)[0]
    mod = importlib.import_module("subliminal_patch.providers.%s" % module_name.lower())
    for item in dir(mod):
        cls = getattr(mod, item)
        if item != "Provider" and item.endswith("Provider") and not item.startswith("_"):
            is_sz_provider = issubclass(cls, Provider)
            is_provider = issubclass(cls, _Provider)

            if not is_provider:
                continue

            if not is_sz_provider:
                # patch provider bases
                new_bases = []

                for base in cls.__bases__:
                    if base == _Provider:
                        base = Provider
                    else:
                        if _Provider in base.__bases__:
                            base.__bases__ = (Provider,)
                    new_bases.append(base)

                cls.__bases__ = tuple(new_bases)

                # patch subtitle bases
                new_bases = []
                for base in cls.subtitle_class.__bases__:
                    if base == _Subtitle:
                        base = Subtitle
                    else:
                        if _Subtitle in base.__bases__:
                            base.__bases__ = (Subtitle,)
                    new_bases.append(base)

                cls.subtitle_class.__bases__ = tuple(new_bases)

            # inject our requests.Session wrapper for automatic retry
            mod.Session = RetryingSession
            mod.guess_matches = guess_matches

            provider_registry.register(module_name, cls)

    # try patching the correspondent subliminal provider
    try:
        subliminal_mod = importlib.import_module("subliminal.providers.%s" % module_name.lower())
    except ImportError:
        pass
    else:
        subliminal_mod.Session = RetryingSession
        subliminal_mod.guess_matches = guess_matches

