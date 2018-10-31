# coding=utf-8
from collections import OrderedDict


class SubtitleModRegistry(object):
    mods = None
    mods_available = None

    def __init__(self):
        self.mods = OrderedDict()
        self.mods_available = []

    def register(self, mod):
        self.mods[mod.identifier] = mod
        self.mods_available.append(mod.identifier)

registry = SubtitleModRegistry()
