# -*- coding: utf-8 -*-
from pkg_resources import EntryPoint

from stevedore import ExtensionManager


class RegistrableExtensionManager(ExtensionManager):
    """:class:~stevedore.extensions.ExtensionManager` with support for registration.

    It allows loading of internal extensions without setup and registering/unregistering additional extensions.

    Loading is done in this order:

    * Entry point extensions
    * Internal extensions
    * Registered extensions

    :param str namespace: namespace argument for :class:~stevedore.extensions.ExtensionManager`.
    :param list internal_extensions: internal extensions to use with entry point syntax.
    :param \*\*kwargs: additional parameters for the :class:~stevedore.extensions.ExtensionManager` constructor.

    """
    def __init__(self, namespace, internal_extensions, **kwargs):
        #: Registered extensions with entry point syntax
        self.registered_extensions = []

        #: Internal extensions with entry point syntax
        self.internal_extensions = internal_extensions

        super(RegistrableExtensionManager, self).__init__(namespace, **kwargs)

    def _find_entry_points(self, namespace):
        # copy of default extensions
        eps = list(super(RegistrableExtensionManager, self)._find_entry_points(namespace))

        # internal extensions
        for iep in self.internal_extensions:
            ep = EntryPoint.parse(iep)
            if ep.name not in [e.name for e in eps]:
                eps.append(ep)

        # registered extensions
        for rep in self.registered_extensions:
            ep = EntryPoint.parse(rep)
            if ep.name not in [e.name for e in eps]:
                eps.append(ep)

        return eps

    def register(self, entry_point):
        """Register an extension

        :param str entry_point: extension to register (entry point syntax).
        :raise: ValueError if already registered.

        """
        if entry_point in self.registered_extensions:
            raise ValueError('Extension already registered')

        ep = EntryPoint.parse(entry_point)
        if ep.name in self.names():
            raise ValueError('An extension with the same name already exist')

        ext = self._load_one_plugin(ep, False, (), {}, False)
        self.extensions.append(ext)
        if self._extensions_by_name is not None:
            self._extensions_by_name[ext.name] = ext
        self.registered_extensions.insert(0, entry_point)

    def unregister(self, entry_point):
        """Unregister a provider

        :param str entry_point: provider to unregister (entry point syntax).

        """
        if entry_point not in self.registered_extensions:
            raise ValueError('Extension not registered')

        ep = EntryPoint.parse(entry_point)
        self.registered_extensions.remove(entry_point)
        if self._extensions_by_name is not None:
            del self._extensions_by_name[ep.name]
        for i, ext in enumerate(self.extensions):
            if ext.name == ep.name:
                del self.extensions[i]
                break


#: Provider manager
provider_manager = RegistrableExtensionManager('subliminal.providers', [
    'addic7ed = subliminal.providers.addic7ed:Addic7edProvider',
    'legendastv = subliminal.providers.legendastv:LegendasTVProvider',
    'opensubtitles = subliminal.providers.opensubtitles:OpenSubtitlesProvider',
    'podnapisi = subliminal.providers.podnapisi:PodnapisiProvider',
    'shooter = subliminal.providers.shooter:ShooterProvider',
    'subscenter = subliminal.providers.subscenter:SubsCenterProvider',
    'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
    'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider'
])

#: Refiner manager
refiner_manager = RegistrableExtensionManager('subliminal.refiners', [
    'metadata = subliminal.refiners.metadata:refine',
    'omdb = subliminal.refiners.omdb:refine',
    'tvdb = subliminal.refiners.tvdb:refine'
])
