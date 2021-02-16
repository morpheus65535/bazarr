# coding=utf-8
from __future__ import absolute_import
import re
import logging

from subzero.modification.exc import EmptyEntryError
from subzero.modification.processors import Processor

logger = logging.getLogger(__name__)


class ReProcessor(Processor):
    """
    Regex processor
    """
    pattern = None
    replace_with = None

    def __init__(self, pattern, replace_with, name=None, supported=None, entry=False, **kwargs):
        super(ReProcessor, self).__init__(name=name, supported=supported)
        self.pattern = pattern
        self.replace_with = replace_with
        self.use_entry = entry

    def process(self, content, debug=False, entry=None, **kwargs):
        if not self.use_entry:
            return self.pattern.sub(self.replace_with, content)

        ret = self.pattern.sub(self.replace_with, entry)
        if not ret:
            raise EmptyEntryError()
        elif ret != entry:
            return ret
        return content


class NReProcessor(ReProcessor):
    pass


class MultipleWordReProcessor(ReProcessor):
    """
    Expects a dictionary in the form of:
    dict = {
        "data": {"old_value": "new_value"},
        "pattern": compiled re object that matches data.keys()
    }
    replaces found key in pattern with the corresponding value in data
    """
    def __init__(self, snr_dict, name=None, parent=None, supported=None, **kwargs):
        super(ReProcessor, self).__init__(name=name, supported=supported)
        self.snr_dict = snr_dict

    def process(self, content, debug=False, **kwargs):
        if not self.snr_dict["data"]:
            return content

        return self.snr_dict["pattern"].sub(lambda x: self.snr_dict["data"][x.group(0)], content)

