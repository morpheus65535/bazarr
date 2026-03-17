# coding=utf-8

from __future__ import absolute_import
import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry

logger = logging.getLogger(__name__)


class TwoPointFit(SubtitleModification):
    identifier = "two_point_fit"
    description = "Use first and last sentences to linearly align timing of the subtitles"
    exclusive = False
    advanced = True
    modifies_whole_file = True

    def modify(self, content, debug=False, parent=None, **kwargs):

        """
        Place first sentence at 00:00:00 and scale until duration matches, then offset back
        """

        parent.f.shift(h=-int(kwargs.get("rh", 0)), m=-int(kwargs.get("rm", 0)), s=-int(kwargs.get("rs", 0)), ms=-int(kwargs.get("rms", 0)))
        parent.f.transform_framerate(float(kwargs.get("from")), float(kwargs.get("to")))
        parent.f.shift(h=int(kwargs.get("oh", 0)), m=int(kwargs.get("om", 0)), s=int(kwargs.get("os", 0)), ms=int(kwargs.get("oms", 0)))

registry.register(TwoPointFit)
