# coding=utf-8
import re
import logging

from subzero.modification.processors.re_processor import ReProcessor, NReProcessor

logger = logging.getLogger(__name__)


class SubtitleModification(object):
    identifier = None
    description = None
    long_description = None
    exclusive = False
    advanced = False  # has parameters
    args_mergeable = False
    order = None
    modifies_whole_file = False  # operates on the whole file, not individual entries
    apply_last = False
    only_uppercase = False
    pre_processors = []
    processors = []
    post_processors = []
    last_processors = []
    languages = []

    def __init__(self, parent):
        return

    def _process(self, content, processors, debug=False, parent=None, index=None, **kwargs):
        if not content:
            return

        # processors may be a list or a callable
        #if callable(processors):
        #    _processors = processors()
        #else:
        #    _processors = processors
        _processors = processors

        new_content = content
        for processor in _processors:
            if not processor.supported(parent):
                if debug and processor.enabled:
                    logger.debug("Processor not supported, skipping: %s", processor.name)
                    processor.enabled = False
                continue

            old_content = new_content
            new_content = processor.process(new_content, debug=debug, **kwargs)
            if not new_content:
                if debug:
                    logger.debug("Processor returned empty line: %s", processor.name)
                break
            if debug:
                if old_content == new_content:
                    continue
                logger.debug("%d: %s: %s -> %s", index, processor.name, repr(old_content), repr(new_content))

        return new_content

    def pre_process(self, content, debug=False, parent=None, **kwargs):
        return self._process(content, self.pre_processors, debug=debug, parent=parent, **kwargs)

    def process(self, content, debug=False, parent=None, **kwargs):
        return self._process(content, self.processors, debug=debug, parent=parent, **kwargs)

    def post_process(self, content, debug=False, parent=None, **kwargs):
        return self._process(content, self.post_processors, debug=debug, parent=parent, **kwargs)

    def modify(self, content, debug=False, parent=None, procs=None, **kwargs):
        if not content:
            return

        new_content = content
        for method in procs or ("pre_process", "process", "post_process"):
            if not new_content:
                return
            new_content = self._process(new_content, getattr(self, "%sors" % method),
                                        debug=debug, parent=parent, **kwargs)

        return new_content

    @classmethod
    def get_signature(cls, **kwargs):
        string_args = ",".join(["%s=%s" % (key, value) for key, value in kwargs.iteritems()])
        return "%s(%s)" % (cls.identifier, string_args)

    @classmethod
    def merge_args(cls, args1, args2):
        raise NotImplementedError


class SubtitleTextModification(SubtitleModification):
    pass


TAG = ur"(?:\s*{\\[iusb][0-1]}\s*)*"
EMPTY_TAG_PROCESSOR = ReProcessor(re.compile(r'({\\\w1})[\s.,-_!?]*({\\\w0})'), "", name="empty_tag")

empty_line_post_processors = [
    # empty tag
    EMPTY_TAG_PROCESSOR,

    # empty line (needed?)
    NReProcessor(re.compile(r'^[\s-]+$'), "", name="empty_line"),
]


class EmptyEntryError(Exception):
    pass


class EmptyLineError(Exception):
    pass
