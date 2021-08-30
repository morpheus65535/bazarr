# coding=utf-8

from __future__ import absolute_import
import logging

from subzero.modification.mods import SubtitleModification
from subzero.modification import registry
import six

logger = logging.getLogger(__name__)


class ShiftOffset(SubtitleModification):
    identifier = "shift_offset"
    description = "Change the timing of the subtitle"
    exclusive = False
    advanced = True
    args_mergeable = True
    modifies_whole_file = True

    long_description = "Adds or substracts a certain amount of time from the whole subtitle to match your media"

    @classmethod
    def merge_args(cls, args1, args2):
        new_args = dict((key, int(value)) for key, value in six.iteritems(args1))

        for key, value in six.iteritems(args2):
            if not int(value):
                continue

            if key in new_args:
                new_args[key] += int(value)
            else:
                new_args[key] = int(value)

        return dict([k_v for k_v in six.iteritems(new_args) if bool(k_v[1])])

    def modify(self, content, debug=False, parent=None, **kwargs):
        parent.f.shift(h=int(kwargs.get("h", 0)), m=int(kwargs.get("m", 0)), s=int(kwargs.get("s", 0)),
                       ms=int(kwargs.get("ms", 0)))


registry.register(ShiftOffset)
