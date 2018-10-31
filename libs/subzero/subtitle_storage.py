# coding=utf-8
import datetime
import gzip
import hashlib
import os
import logging
import traceback
import types
import zlib

import sys

from json_tricks.nonp import loads
from subzero.lib.json import dumps
from scandir import scandir, scandir_generic as _scandir_generic
from constants import mode_map

logger = logging.getLogger(__name__)


class JSONStoredSubtitle(object):
    score = None
    storage_type = None
    hash = None
    provider_name = None
    id = None
    date_added = None
    mode = "a"  # auto/manual/auto-better (a/m/b)
    content = None
    mods = None
    encoding = None
    last_mod = None  # file modification

    def initialize(self, score, storage_type, hash, provider_name, id, date_added=None, mode="a", content=None,
                 mods=None, encoding=None, last_mod=None):
        self.score = int(score)
        self.storage_type = storage_type
        self.hash = hash
        self.provider_name = provider_name
        self.id = id
        self.date_added = date_added or datetime.datetime.now()
        self.mode = mode
        self.content = content
        self.mods = mods or []
        self.encoding = encoding
        self.last_mod = last_mod

    def add_mod(self, identifier):
        self.mods = self.mods or []
        if identifier is None:
            self.mods = []
            return

        self.mods.append(identifier)

    @classmethod
    def get_mode_verbose(cls, mode):
        return mode_map.get(mode, "Unknown")

    @property
    def mode_verbose(self):
        return self.get_mode_verbose(self.mode)

    def serialize(self):
        return self.__dict__

    def deserialize(self, data):
        if data["content"]:
            # legacy: storage was unicode; content is always present in encoded form
            if isinstance(data["content"], types.UnicodeType):
                data["content"] = data["content"].encode(data["encoding"])

        self.initialize(**data)

    @property
    def key(self):
        return self.provider_name, self.id


class JSONStoredVideoSubtitles(object):
    """
    manages stored subtitles for video_id per media_part/language combination
    """
    video_id = None  # rating_key
    title = None
    parts = None
    version = None
    item_type = None  # movie / episode
    added_at = None

    def initialize(self, plex_item, version=None):
        self.video_id = str(plex_item.rating_key)

        self.title = plex_item.title
        self.parts = {}
        self.version = version
        self.item_type = plex_item.type
        self.added_at = datetime.datetime.fromtimestamp(plex_item.added_at)

    def deserialize(self, data):
        parts = data.pop("parts")
        self.parts = {}
        self.__dict__.update(data)

        if parts:
            for part_id, part in parts.iteritems():
                self.parts[part_id] = {}
                for language, sub_data in part.iteritems():
                    self.parts[part_id][language] = {}

                    for sub_key, subtitle_data in sub_data.iteritems():
                        if sub_key == "current":
                            if not isinstance(subtitle_data, tuple):
                                subtitle_data = tuple(subtitle_data.split("__"))
                            self.parts[part_id][language]["current"] = subtitle_data
                        elif sub_key == "blacklist":
                            bl = dict((tuple([str(a) for a in k.split("__")]), v) for k, v in subtitle_data.iteritems())
                            self.parts[part_id][language]["blacklist"] = bl
                        else:
                            sub = JSONStoredSubtitle()

                            sub.initialize(**subtitle_data)
                            if not isinstance(sub_key, tuple):
                                sub_key = tuple(sub_key.split("__"))

                            self.parts[part_id][language][sub_key] = sub

    def serialize(self):
        data = {"parts": {}}
        for key, value in self.__dict__.iteritems():
            if key != "parts":
                data[key] = value

        for part_id, part in self.parts.iteritems():
            data["parts"][part_id] = {}
            for language, sub_data in part.iteritems():
                data["parts"][part_id][language] = {}

                for sub_key, stored_subtitle in sub_data.iteritems():
                    if sub_key == "current":
                        data["parts"][part_id][language]["current"] = "__".join(stored_subtitle)
                    elif sub_key == "blacklist":
                        data["parts"][part_id][language]["blacklist"] = dict(("__".join(k), v) for k, v in
                                                                             stored_subtitle.iteritems())
                    else:
                        if stored_subtitle.content and not stored_subtitle.encoding:
                            continue

                        serialized_sub = stored_subtitle.serialize()
                        if serialized_sub:
                            data["parts"][part_id][language]["__".join(sub_key)] = serialized_sub

        return data

    def add(self, part_id, lang, subtitle, storage_type, date_added=None, mode="a", last_mod=None, set_current=True):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            self.parts[part_id] = {}
            part = self.parts[part_id]

        subs = part.get(lang)
        if not subs:
            part[lang] = {}
            subs = part[lang]

        sub_key = self.get_sub_key(subtitle.provider_name, subtitle.id)
        subs[sub_key] = JSONStoredSubtitle()
        subs[sub_key].initialize(subtitle.score, storage_type, hashlib.md5(subtitle.content).hexdigest(),
                                 subtitle.provider_name, subtitle.id, date_added=date_added, mode=mode,
                                 content=subtitle.content, mods=subtitle.mods, encoding="utf-8",
                                 last_mod=last_mod)

        if set_current:
            logger.debug(u"Setting subtitle as current: %r", subtitle)
            subs["current"] = sub_key

        return True

    def get_any(self, part_id, lang):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            return

        subs = part.get(str(lang))
        if not subs:
            return

        if "current" in subs and subs["current"]:
            return subs.get(subs["current"])

    def get(self, part_id, lang, sub_key):
        subs = self.get_all(part_id, lang)
        if not subs:
            return

        return subs.get(sub_key)

    def get_all(self, part_id, lang):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            return

        return part.get(str(lang))

    def set_current(self, part_id, lang, sub_key):
        subs = self.get_all(part_id, lang)
        if not subs:
            return

        if sub_key not in subs:
            logger.info("Tried setting unknown subtitle %s as current" % sub_key)
            return

        subs["current"] = sub_key
        logger.debug("Set subtitle %s as current for %s, %s" % (sub_key, part_id, lang))

    def get_by_provider(self, part_id, lang, provider_name):
        out = []
        all_subs = self.get_all(part_id, lang)
        if not all_subs:
            return out

        for key, subtitle in all_subs.iteritems():
            if key in ("current", "blacklist"):
                continue

            if subtitle.provider_name == provider_name:
                out.append(subtitle)
        return out

    def count(self, part_id, lang):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            return 0

        subs = part.get(str(lang))
        return len(filter(lambda key: key not in ("current", "blacklist"), subs.keys()))

    def get_sub_key(self, provider_name, id):
        return provider_name, str(id)

    def get_blacklist(self, part_id, lang):
        part_id = str(part_id)
        part = self.parts.get(part_id)
        if not part:
            return {}, {}

        subs = part.get(str(lang))
        if not subs:
            return {}, {}

        current_bl = subs.get("blacklist", {})
        return current_bl, subs

    def blacklist(self, part_id, lang, sub_key, add=True):
        current_bl, subs = self.get_blacklist(part_id, lang)
        sub = subs.get(subs["current"])
        if not sub:
            return

        if sub_key in current_bl:
            if add:
                return
            else:
                del current_bl[sub_key]
                subs["blacklist"] = current_bl
                return

        current_bl[sub_key] = {"date_added": sub.date_added, "score": sub.score, "mode": sub.mode, "storage_type":
            sub.storage_type}
        subs["blacklist"] = current_bl

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.video_id)

    def __str__(self):
        return str(self.video_id)


class StoredSubtitlesManager(object):
    """
    manages the storage and retrieval of StoredVideoSubtitles instances for a given video_id
    """
    storage = None
    version = 3
    extension = ".json.gz"

    def __init__(self, storage, threadkit, plexapi_item_getter):
        self.storage = storage
        self.get_item = plexapi_item_getter
        self.threadkit = threadkit

    def destroy(self):
        self.storage = None
        self.get_item = None
        self.threadkit = None

    def get_storage_filename(self, video_id):
        return "subs_%s" % video_id

    @property
    def dataitems_path(self):
        return os.path.join(getattr(self.storage, "_core").storage.data_path, "DataItems")

    def get_json_data_path(self, bare_fn):
        if not bare_fn.endswith(self.extension):
            return os.path.join(self.dataitems_path, "%s%s" % (bare_fn, self.extension))
        return os.path.join(self.dataitems_path, bare_fn)

    def get_all_files(self, scandir_generic=False):
        _scandir = _scandir_generic if scandir_generic else scandir
        for entry in _scandir(self.dataitems_path):
            if entry.is_file(follow_symlinks=False) and \
                    entry.name.startswith("subs_") and \
                    entry.name.endswith(self.extension):
                yield entry.name

    def get_recent_files(self, age_days=30):
        fl = []
        root = self.dataitems_path
        recent_dt = datetime.datetime.now() - datetime.timedelta(days=age_days)

        def run(scandir_generic=False):
            for fn in self.get_all_files(scandir_generic=scandir_generic):
                ctime = os.path.getctime(os.path.join(root, fn))
                created = datetime.datetime.fromtimestamp(ctime)
                if created > recent_dt:
                    fl.append(fn)
        try:
            run()
        except OSError:
            run(scandir_generic=True)
        return fl

    def load_recent_files(self, age_days=30):
        fl = self.get_recent_files(age_days=age_days)
        out = {}
        for fn in fl:
            data = self.load(filename=fn)
            if data:
                out[fn] = data
        return out

    def delete_missing(self, wanted_languages=set(), scandir_generic=False):
        deleted = []

        def delete_fn(filename):
            if filename.endswith(self.extension):
                self.delete(self.get_json_data_path(filename))
            else:
                self.legacy_delete(filename)

        for fn in self.get_all_files(scandir_generic=scandir_generic):
            video_id = os.path.basename(fn).split(".")[0].split("subs_")[1]
            item = self.get_item(video_id)

            # item missing, delete storage
            if not item:
                delete_fn(fn)
                deleted.append(video_id)

            else:
                known_parts = []

                # wrong (legacy) info, delete storage
                if not hasattr(item, "media"):
                    delete_fn(fn)
                    deleted.append(video_id)
                    continue

                for media in item.media:
                    for part in media.parts:
                        known_parts.append(str(part.id))
                stored_subs = self.load(filename=fn)

                if not stored_subs:
                    continue

                missing_parts = set(stored_subs.parts).difference(set(known_parts))

                changed_any = False

                # remove known info about deleted parts
                if missing_parts:
                    logger.debug("Parts removed: %s:%s, removing data", video_id, missing_parts)
                    for missing_part in missing_parts:
                        if missing_part in stored_subs.parts:
                            try:
                                del stored_subs.parts[missing_part]
                                changed_any = True
                            except:
                                pass

                # remove known info about non-existing languages
                for part_id, part in stored_subs.parts.iteritems():
                    missing_languages = set(part).difference(wanted_languages)
                    if missing_languages:
                        logger.debug("Languages removed: %s:%s:%s, removing data", video_id, part_id, missing_languages)
                        for missing_language in missing_languages:
                            try:
                                del stored_subs.parts[part_id][missing_language]
                                changed_any = True
                            except:
                                pass

                if changed_any:
                    self.save(stored_subs)
                stored_subs = None
                missing_parts = None
                missing_languages = None

        return deleted

    def migrate_v2(self, subs_for_video):
        plex_item = self.get_item(subs_for_video.video_id)
        if not plex_item:
            return False
        subs_for_video.item_type = plex_item.type
        subs_for_video.added_at = datetime.datetime.fromtimestamp(plex_item.added_at)
        subs_for_video.version = 2
        return True

    def migrate_v3(self, subs_for_video):
        subs_for_video.version = 3
        return True

    def load(self, video_id=None, filename=None):
        subs_for_video = None
        bare_fn = self.get_storage_filename(video_id) if video_id else filename
        json_path = self.get_json_data_path(bare_fn)
        basename = os.path.basename(json_path)

        #logger.debug("Loading subtitle storage data file: %s", basename)

        if os.path.exists(json_path):
            # new style data
            subs_for_video = JSONStoredVideoSubtitles()
            try:
                with self.threadkit.Lock(key="sub_storage_%s" % basename):
                    if sys.platform == "win32":
                        try:
                            with open(json_path, 'rb') as f:
                                s = zlib.decompress(f.read())
                        except zlib.error:
                            # fallback to old gzip win32 implementation
                            with gzip.open(json_path, 'rb', compresslevel=6) as f:
                                s = f.read()

                    else:
                        with gzip.open(json_path, 'rb', compresslevel=6) as f:
                            s = f.read()

                data = loads(s)
            except:
                logger.error("Couldn't load JSON data for %s: %s", bare_fn, traceback.format_exc())
                return

            subs_for_video.deserialize(data)
            data = None

        if not subs_for_video:
            return

        # apply possible migrations
        cur_ver = old_ver = subs_for_video.version

        if cur_ver < self.version:
            success = False
            while cur_ver < self.version:
                cur_ver += 1
                mig_func = "migrate_v%s" % cur_ver
                if hasattr(self, mig_func):
                    logger.info("Migrating subtitle storage for %s %s>%s" % (subs_for_video.video_id, old_ver, cur_ver))
                    success = getattr(self, mig_func)(subs_for_video)
                    if success is False:
                        logger.error("Couldn't migrate %s, removing data", subs_for_video.video_id)
                        self.delete(json_path)
                        break

            if cur_ver > old_ver and success:
                logger.info("Storing migrated subtitle storage for %s" % subs_for_video.video_id)
                self.save(subs_for_video)
            elif not success:
                logger.info("Migration of %s %s>%s failed" % (subs_for_video.video_id, old_ver, cur_ver))

        return subs_for_video

    def new(self, plex_item):
        subs_for_video = JSONStoredVideoSubtitles()
        subs_for_video.initialize(plex_item, version=self.version)
        return subs_for_video

    def load_or_new(self, plex_item, save=False):
        subs_for_video = self.load(plex_item.rating_key)
        if not subs_for_video:
            logger.info("Creating new subtitle storage for: %s", plex_item.rating_key)
            subs_for_video = self.new(plex_item)
            if save:
                self.save(subs_for_video)
        return subs_for_video

    def save(self, subs_for_video):
        data = subs_for_video.serialize()
        temp_fn = self.get_json_data_path(self.get_storage_filename(subs_for_video.video_id) + "_tmp")
        fn = self.get_json_data_path(self.get_storage_filename(subs_for_video.video_id))
        basename = os.path.basename(fn)
        json_data = str(dumps(data, ensure_ascii=False))
        with self.threadkit.Lock(key="sub_storage_%s" % basename):
            if sys.platform == "win32":
                try:
                    f = open(temp_fn, "w+b")

                    try:
                        f.seek(0, os.SEEK_CUR)
                        f.write(zlib.compress(json_data, 6))
                        f.flush()
                    except:
                        logger.error("Something went wrong when writing to: %s: %s", basename, traceback.format_exc())
                    finally:
                        f.close()
                except:
                    logger.error("Something went REALLY wrong when writing to: %s: %s", basename,
                                 traceback.format_exc())
            else:
                with gzip.open(temp_fn, "wb", compresslevel=6) as f:
                    f.write(json_data)

            os.rename(temp_fn, fn)

    def delete(self, filename):
        os.remove(filename)

    def legacy_delete(self, filename):
        try:
            self.storage.Remove(filename)
        except:
            logger.error("Failed to delete item %s: %s" % (filename, traceback.format_exc()))
