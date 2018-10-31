# coding=utf-8

import logging
from collections import OrderedDict

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


COLOR_MAP = OrderedDict([
    ("white", "#FFFFFF"),
    ("light-grey", "#C0C0C0"),
    ("red", "#FF0000"),
    ("green", "#00FF00"),
    ("yellow", "#FFFF00"),
    ("blue", "#0000FF"),
    ("magenta", "#FF00FF"),
    ("cyan", "#00FFFF"),
    ("black", "#000000"),
    ("dark-red", "#800000"),
    ("dark-green", "#008000"),
    ("dark-yellow", "#808000"),
    ("dark-blue", "#000080"),
    ("dark-magenta", "#800080"),
    ("dark-cyan", "#008080"),
    ("dark-grey", "#808080"),
])


class Color(SubtitleModification):
    identifier = "color"
    description = "Change the color of the subtitle"
    exclusive = True
    advanced = True
    modifies_whole_file = True
    apply_last = True

    colors = COLOR_MAP

    long_description = "Adds the requested color to every line of the subtitle. Support depends on player."

    def modify(self, content, debug=False, parent=None, **kwargs):
        color = self.colors.get(kwargs.get("name"))
        if color:
            for entry in parent.f:
                entry.text = u'<font color="%s">%s</font>' % (color, entry.text)


registry.register(Color)
