# coding=utf-8

import traceback
import re
import pysubs2
import logging
import time

from mods import EMPTY_TAG_PROCESSOR, EmptyEntryError
from registry import registry
from subzero.language import Language

logger = logging.getLogger(__name__)


lowercase_re = re.compile(ur'(?sux)[a-zà-ž]')


class SubtitleModifications(object):
    debug = False
    language = None
    initialized_mods = {}
    mods_used = []
    only_uppercase = False
    f = None

    font_style_tag_start = u"{\\"

    def __init__(self, debug=False):
        self.debug = debug
        self.initialized_mods = {}
        self.mods_used = []

    def load(self, fn=None, content=None, language=None, encoding="utf-8"):
        """
        
        :param encoding: used for decoding the content when fn is given, not used in case content is given
        :param language: babelfish.Language language of the subtitle
        :param fn:  filename
        :param content: unicode 
        :return: 
        """
        if language:
            self.language = Language.rebuild(language, forced=False)
        self.initialized_mods = {}
        try:
            if fn:
                self.f = pysubs2.load(fn, encoding=encoding)
            elif content:
                self.f = pysubs2.SSAFile.from_string(content)
        except (IOError,
                UnicodeDecodeError,
                pysubs2.exceptions.UnknownFPSError,
                pysubs2.exceptions.UnknownFormatIdentifierError,
                pysubs2.exceptions.FormatAutodetectionError):
            if fn:
                logger.exception("Couldn't load subtitle: %s: %s", fn, traceback.format_exc())
            elif content:
                logger.exception("Couldn't load subtitle: %s", traceback.format_exc())

        return bool(self.f)

    @classmethod
    def parse_identifier(cls, identifier):
        # simple identifier
        if identifier in registry.mods:
            return identifier, {}

        # identifier with params; identifier(param=value)
        split_args = identifier[identifier.find("(")+1:-1].split(",")
        args = dict((key, value) for key, value in [sub.split("=") for sub in split_args])
        return identifier[:identifier.find("(")], args

    @classmethod
    def get_mod_class(cls, identifier):
        identifier, args = cls.parse_identifier(identifier)
        return registry.mods[identifier]

    @classmethod
    def get_mod_signature(cls, identifier, **kwargs):
        return cls.get_mod_class(identifier).get_signature(**kwargs)

    def prepare_mods(self, *mods):
        parsed_mods = [(SubtitleModifications.parse_identifier(mod), mod) for mod in mods]
        final_mods = {}
        line_mods = []
        non_line_mods = []
        used_mods = []
        mods_merged = {}
        mods_merged_log = {}

        for mod_data, orig_identifier in parsed_mods:
            identifier, args = mod_data
            if identifier not in registry.mods:
                logger.error("Mod %s not loaded", identifier)
                continue

            mod_cls = registry.mods[identifier]
            # exclusive mod, kill old, use newest
            if identifier in final_mods and mod_cls.exclusive:
                final_mods.pop(identifier)

            # language-specific mod, check validity
            if mod_cls.languages and self.language not in mod_cls.languages:
                if self.debug:
                    logger.debug("Skipping %s, because %r is not a valid language for this mod",
                                 identifier, self.language)
                continue

            if mod_cls.only_uppercase and not self.only_uppercase:
                if self.debug:
                    logger.debug("Skipping %s, because the subtitle isn't all uppercase", identifier)
                continue

            # merge args of duplicate mods if possible
            elif mod_cls.args_mergeable and identifier in mods_merged:
                mods_merged[identifier] = mod_cls.merge_args(mods_merged[identifier], args)
                mods_merged_log[identifier]["identifiers"].append(orig_identifier)
                continue

            if mod_cls.args_mergeable:
                mods_merged[identifier] = mod_cls.merge_args(args, {})
                mods_merged_log[identifier] = {"identifiers": [orig_identifier], "final_identifier": orig_identifier}
                used_mods.append("%s_ORIG_POSITION" % identifier)
                continue

            final_mods[identifier] = args
            used_mods.append(orig_identifier)

        # finalize merged mods into final and used mods
        for identifier, args in mods_merged.iteritems():
            pos_preserve_index = used_mods.index("%s_ORIG_POSITION" % identifier)

            # clear empty mods after merging
            if not any(args.values()):
                if self.debug:
                    logger.debug("Skipping %s, empty args", identifier)

                if pos_preserve_index > -1:
                    used_mods.pop(pos_preserve_index)

                mods_merged_log.pop(identifier)
                continue

            # clear empty args
            final_mod_args = dict(filter(lambda (k, v): bool(v), args.iteritems()))

            _data = SubtitleModifications.get_mod_signature(identifier, **final_mod_args)
            if _data == mods_merged_log[identifier]["final_identifier"]:
                mods_merged_log.pop(identifier)
            else:
                mods_merged_log[identifier]["final_identifier"] = _data

            if pos_preserve_index > -1:
                used_mods[pos_preserve_index] = _data
            else:
                # should never happen
                used_mods.append(_data)
            final_mods[identifier] = args

        if self.debug:
            for identifier, data in mods_merged_log.iteritems():
                logger.debug("Merged %s to %s", data["identifiers"], data["final_identifier"])

        # separate all mods into line and non-line mods
        for identifier, args in final_mods.iteritems():
            mod_cls = registry.mods[identifier]
            if mod_cls.modifies_whole_file:
                non_line_mods.append((identifier, args))
            else:
                line_mods.append((mod_cls.order, identifier, args))

            # initialize the mods
            if identifier not in self.initialized_mods:
                self.initialized_mods[identifier] = mod_cls(self)

        return line_mods, non_line_mods, used_mods

    def detect_uppercase(self):
        entries_used = 0
        for entry in self.f:
            entry_used = False
            for sub in entry.text.strip().split("\N"):
                # skip HI bracket entries, those might actually be lowercase
                sub = sub.strip()
                for processor in registry.mods["remove_HI"].processors[:4]:
                    sub = processor.process(sub)

                if sub.strip():
                    if lowercase_re.search(sub):
                        return False

                    entry_used = True
                else:
                    # skip full entry
                    break

            if entry_used:
                entries_used += 1

            if entries_used == 40:
                break

        return True

    def modify(self, *mods):
        new_entries = []
        start = time.time()
        self.only_uppercase = self.detect_uppercase()

        if self.only_uppercase and self.debug:
            logger.debug("Full-uppercase subtitle found")

        line_mods, non_line_mods, mods_used = self.prepare_mods(*mods)
        self.mods_used = mods_used

        # apply non-last file mods
        if non_line_mods:
            non_line_mods_start = time.time()
            self.apply_non_line_mods(non_line_mods)

            if self.debug:
                logger.debug("Non-Line mods took %ss", time.time() - non_line_mods_start)

        # sort line mods
        line_mods.sort(key=lambda x: (x is None, x))

        # apply line mods
        if line_mods:
            line_mods_start = time.time()
            self.apply_line_mods(new_entries, line_mods)

            if self.debug:
                logger.debug("Line mods took %ss", time.time() - line_mods_start)

            if new_entries:
                self.f.events = new_entries

        # apply last file mods
        if non_line_mods:
            non_line_mods_start = time.time()
            self.apply_non_line_mods(non_line_mods, only_last=True)

            if self.debug:
                logger.debug("Final Non-Line mods took %ss", time.time() - non_line_mods_start)

        if self.debug:
            logger.debug("Subtitle Modification took %ss", time.time() - start)
            logger.debug("Mods applied: %s" % self.mods_used)

    def apply_non_line_mods(self, mods, only_last=False):
        for identifier, args in mods:
            mod = self.initialized_mods[identifier]
            if (not only_last and not mod.apply_last) or (only_last and mod.apply_last):
                if self.debug:
                    logger.debug("Applying %s", identifier)
                mod.modify(None, debug=self.debug, parent=self, **args)

    def apply_line_mods(self, new_entries, mods):
        for index, entry in enumerate(self.f, 1):
            applied_mods = []
            lines = []

            line_count = 0
            start_tags = []
            end_tags = []

            t = entry.text.strip()
            if not t:
                if self.debug:
                    logger.debug(u"Skipping empty line: %s", index)
                continue

            skip_entry = False
            for line in t.split(ur"\N"):
                # don't bother the mods with surrounding tags
                old_line = line
                line = line.strip()
                skip_line = False
                line_count += 1

                if not line:
                    continue

                # clean {\X0} tags before processing
                # fixme: handle nested tags?
                start_tag = u""
                end_tag = u""
                if line.startswith(self.font_style_tag_start):
                    start_tag = line[:5]
                    line = line[5:]
                if line[-5:-3] == self.font_style_tag_start:
                    end_tag = line[-5:]
                    line = line[:-5]

                last_procs_mods = []

                # fixme: this double loop is ugly
                for order, identifier, args in mods:
                    mod = self.initialized_mods[identifier]

                    try:
                        line = mod.modify(line.strip(), entry=entry.text, debug=self.debug, parent=self, index=index,
                                          **args)
                    except EmptyEntryError:
                        if self.debug:
                            logger.debug(u"%d: %s: %r -> ''", index, identifier, entry.text)
                        skip_entry = True
                        break

                    if not line:
                        if self.debug:
                            logger.debug(u"%d: %s: %r -> ''", index, identifier, old_line)
                        skip_line = True
                        break

                    applied_mods.append(identifier)
                    if mod.last_processors:
                        last_procs_mods.append([identifier, args])

                if skip_entry:
                    lines = []
                    break

                if skip_line:
                    continue

                for identifier, args in last_procs_mods:
                    mod = self.initialized_mods[identifier]

                    try:
                        line = mod.modify(line.strip(), entry=entry.text, debug=self.debug, parent=self, index=index,
                                          procs=["last_process"], **args)
                    except EmptyEntryError:
                        if self.debug:
                            logger.debug(u"%d: %s: %r -> ''", index, identifier, entry.text)
                        skip_entry = True
                        break

                    if not line:
                        if self.debug:
                            logger.debug(u"%d: %s: %r -> ''", index, identifier, old_line)
                        skip_line = True
                        break

                if skip_entry:
                    lines = []
                    break

                if skip_line:
                    continue

                if start_tag:
                    start_tags.append(start_tag)

                if end_tag:
                    end_tags.append(end_tag)

                # append new line and clean possibly newly added empty tags
                cleaned_line = EMPTY_TAG_PROCESSOR.process(start_tag + line + end_tag, debug=self.debug).strip()
                if cleaned_line:
                    # we may have a single closing tag, if so, try appending it to the previous line
                    if len(cleaned_line) == 5 and cleaned_line.startswith("{\\") and cleaned_line.endswith("0}"):
                        if lines:
                            prev_line = lines.pop()
                            lines.append(prev_line + cleaned_line)
                            continue

                    lines.append(cleaned_line)
                else:
                    if self.debug:
                        logger.debug(u"%d: Ditching now empty line (%r)", index, line)

            if not lines:
                # don't bother logging when the entry only had one line
                if self.debug and line_count > 1:
                    logger.debug(u"%d: %r -> ''", index, entry.text)
                continue

            new_text = ur"\N".join(lines)

            # cheap man's approach to avoid open tags
            add_start_tags = []
            add_end_tags = []
            if len(start_tags) != len(end_tags):
                for tag in start_tags:
                    end_tag = tag.replace("1", "0")
                    if end_tag not in end_tags and new_text.count(tag) > new_text.count(end_tag):
                        add_end_tags.append(end_tag)
                for tag in end_tags:
                    start_tag = tag.replace("0", "1")
                    if start_tag not in start_tags and new_text.count(tag) > new_text.count(start_tag):
                        add_start_tags.append(start_tag)

                if add_end_tags or add_start_tags:
                    entry.text = u"".join(add_start_tags) + new_text + u"".join(add_end_tags)
                    if self.debug:
                        logger.debug(u"Fixing tags: %s (%r -> %r)", str(add_start_tags+add_end_tags), new_text,
                                     entry.text)
                else:
                    entry.text = new_text
            else:
                entry.text = new_text

            new_entries.append(entry)

SubMod = SubtitleModifications




