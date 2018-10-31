# coding=utf-8

import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


class ChangeFPS(SubtitleModification):
    identifier = "change_FPS"
    description = "Change the FPS of the subtitle"
    exclusive = True
    advanced = True
    modifies_whole_file = True

    long_description = "Re-syncs the subtitle to the framerate of the current media file."

    def modify(self, content, debug=False, parent=None, **kwargs):
        fps_from = kwargs.get("from")
        fps_to = kwargs.get("to")
        parent.f.transform_framerate(float(fps_from), float(fps_to))

registry.register(ChangeFPS)
