# coding=utf-8
from collections import OrderedDict

import subliminal
import babelfish


class ProviderRegistry(object):
    providers = None

    def __init__(self):
        self.providers = OrderedDict()

    def __cmp__(self, d):
        return cmp(self.providers, d)

    def __contains__(self, item):
        return item in self.providers

    def __setitem__(self, key, item):
        self.providers[key] = item

    def __iter__(self):
        return iter(self.providers)

    def __getitem__(self, key):
        if key in self.providers:
            return self.providers[key]

    def __repr__(self):
        return repr(self.providers)

    def __str__(self):
        return str(self.providers)

    def __len__(self):
        return len(self.providers)

    def __delitem__(self, key):
        del self.providers[key]

    def register(self, name, cls):
        self.providers[name] = cls

    def names(self):
        return self.providers.keys()


provider_registry = ProviderRegistry()

# add language converters
try:
    babelfish.language_converters.unregister('addic7ed = subliminal.converters.addic7ed:Addic7edConverter')
except ValueError:
    pass

babelfish.language_converters.register('addic7ed = subliminal_patch.language:PatchedAddic7edConverter')
babelfish.language_converters.register('szopensubtitles = subliminal_patch.language:PatchedOpenSubtitlesConverter')
subliminal.refiner_manager.register('sz_metadata = subliminal_patch.refiners.metadata:refine')
subliminal.refiner_manager.register('sz_omdb = subliminal_patch.refiners.omdb:refine')
subliminal.refiner_manager.register('sz_tvdb = subliminal_patch.refiners.tvdb:refine')
subliminal.refiner_manager.register('drone = subliminal_patch.refiners.drone:refine')
subliminal.refiner_manager.register('filebot = subliminal_patch.refiners.filebot:refine')
subliminal.refiner_manager.register('file_info_file = subliminal_patch.refiners.file_info_file:refine')
subliminal.refiner_manager.register('symlinks = subliminal_patch.refiners.symlinks:refine')

