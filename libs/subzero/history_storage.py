# coding=utf-8

import datetime
import logging
import traceback
import types

from subzero.language import Language

from constants import mode_map

logger = logging.getLogger(__name__)


class SubtitleHistoryItem(object):
    item_title = None
    section_title = None
    rating_key = None
    provider_name = None
    lang_name = None
    lang_data = None
    score = None
    thumb = None
    time = None
    mode = "a"

    def __init__(self, item_title, rating_key, section_title=None, subtitle=None, thumb=None, mode="a", time=None):
        self.item_title = item_title
        self.section_title = section_title
        self.rating_key = str(rating_key)
        self.provider_name = subtitle.provider_name
        self.lang_name = str(subtitle.language.name)
        self.lang_data = str(subtitle.language.alpha3), \
                         str(subtitle.language.country) if subtitle.language.country else None, \
                         str(subtitle.language.script) if subtitle.language.script else None
        self.score = subtitle.score
        self.thumb = thumb
        self.time = time or datetime.datetime.now()
        self.mode = mode

    @property
    def title(self):
        return u"%s: %s" % (self.section_title, self.item_title)

    @property
    def language(self):
        if self.lang_data:
            lang_data = [s if s != "None" else None for s in self.lang_data]
            if lang_data[0]:
                return Language(lang_data[0], country=lang_data[1], script=lang_data[2])

    @property
    def mode_verbose(self):
        return mode_map.get(self.mode, "Unknown")

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (Score: %s)" % (unicode(self.item_title), self.score)

    def __str__(self):
        return str(self.rating_key)

    def __hash__(self):
        return hash((self.rating_key, self.score))

    def __eq__(self, other):
        return (self.rating_key, self.score) == (other.rating_key, other.score)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not (self == other)


class SubtitleHistory(object):
    size = 100
    storage = None
    threadkit = None

    def __init__(self, storage, threadkit, size=100):
        self.size = size
        self.storage = storage
        self.threadkit = threadkit

    def add(self, item_title, rating_key, section_title=None, subtitle=None, thumb=None, mode="a", time=None):
        with self.threadkit.Lock(key="sub_history_add"):
            items = self.items

            item = SubtitleHistoryItem(item_title, rating_key, section_title=section_title, subtitle=subtitle,
                                       thumb=thumb, mode=mode, time=time)

            # insert item
            items.insert(0, item)

            # clamp item amount
            items = items[:self.size]

            # store items
            self.storage.SaveObject("subtitle_history", items)

    @property
    def items(self):
        try:
            items = self.storage.LoadObject("subtitle_history") or []
        except:
            items = []
            logger.error("Failed to load history storage: %s" % traceback.format_exc())

        if not isinstance(items, types.ListType):
            items = []
        else:
            items = items[:]
        return items

    def destroy(self):
        self.storage = None
        self.threadkit = None

