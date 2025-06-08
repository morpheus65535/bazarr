# coding=utf-8

from __future__ import absolute_import
import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


class LinearAlign(SubtitleModification):
    identifier = "linear_align"
    description = "Use two points to linearly align timing of the subtitle"
    exclusive = False
    advanced = True
    modifies_whole_file = True

    long_description = "TODO"

    def modify(self, content, debug=False, parent=None, **kwargs):
        logger.debug(kwargs)
        parent.f.shift(h=int(kwargs.get("h", 0)), m=int(kwargs.get("m", 0)), s=int(kwargs.get("s", 0)), ms=int(kwargs.get("ms", 0)))
        
        #fps_to = kwargs.get("to")
        # parent.f.transform_framerate(1.0, float(fps_to))


registry.register(LinearAlign)
