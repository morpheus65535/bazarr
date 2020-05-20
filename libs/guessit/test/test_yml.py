#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name
import logging
import os
# io.open supports encoding= in python 2.7
from io import open  # pylint: disable=redefined-builtin

import babelfish
import six  # pylint:disable=wrong-import-order
import yaml  # pylint:disable=wrong-import-order
from rebulk.remodule import re
from rebulk.utils import is_iterable

from .. import guessit
from ..options import parse_options
from ..yamlutils import OrderedDictYAMLLoader

logger = logging.getLogger(__name__)

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class EntryResult(object):
    def __init__(self, string, negates=False):
        self.string = string
        self.negates = negates
        self.valid = []
        self.missing = []
        self.different = []
        self.extra = []
        self.others = []

    @property
    def ok(self):
        if self.negates:
            return self.missing or self.different
        return not self.missing and not self.different and not self.extra and not self.others

    @property
    def warning(self):
        if self.negates:
            return False
        return not self.missing and not self.different and self.extra

    @property
    def error(self):
        if self.negates:
            return not self.missing and not self.different and not self.others
        return self.missing or self.different or self.others

    def __repr__(self):
        if self.ok:
            return self.string + ': OK!'
        if self.warning:
            return '%s%s: WARNING! (valid=%i, extra=%i)' % ('-' if self.negates else '', self.string, len(self.valid),
                                                            len(self.extra))
        if self.error:
            return '%s%s: ERROR! (valid=%i, missing=%i, different=%i, extra=%i, others=%i)' % \
                   ('-' if self.negates else '', self.string, len(self.valid), len(self.missing), len(self.different),
                    len(self.extra), len(self.others))

        return '%s%s: UNKOWN! (valid=%i, missing=%i, different=%i, extra=%i, others=%i)' % \
               ('-' if self.negates else '', self.string, len(self.valid), len(self.missing), len(self.different),
                len(self.extra), len(self.others))

    @property
    def details(self):
        ret = []
        if self.valid:
            ret.append('valid=' + str(len(self.valid)))
        for valid in self.valid:
            ret.append(' ' * 4 + str(valid))
        if self.missing:
            ret.append('missing=' + str(len(self.missing)))
        for missing in self.missing:
            ret.append(' ' * 4 + str(missing))
        if self.different:
            ret.append('different=' + str(len(self.different)))
        for different in self.different:
            ret.append(' ' * 4 + str(different))
        if self.extra:
            ret.append('extra=' + str(len(self.extra)))
        for extra in self.extra:
            ret.append(' ' * 4 + str(extra))
        if self.others:
            ret.append('others=' + str(len(self.others)))
        for other in self.others:
            ret.append(' ' * 4 + str(other))
        return ret


class Results(list):
    def assert_ok(self):
        errors = [entry for entry in self if entry.error]
        assert not errors


def files_and_ids(predicate=None):
    files = []
    ids = []

    for (dirpath, _, filenames) in os.walk(__location__):
        if os.path.split(dirpath)[-1] == 'config':
            continue
        if dirpath == __location__:
            dirpath_rel = ''
        else:
            dirpath_rel = os.path.relpath(dirpath, __location__)
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(dirpath_rel, filename)
            if ext == '.yml' and (not predicate or predicate(filepath)):
                files.append(filepath)
                ids.append(os.path.join(dirpath_rel, name))

    return files, ids


class TestYml(object):
    """
    Run tests from yaml files.
    Multiple input strings having same expected results can be chained.
    Use $ marker to check inputs that should not match results.
    """

    options_re = re.compile(r'^([ +-]+)(.*)')

    def _get_unique_id(self, collection, base_id):
        ret = base_id
        i = 2
        while ret in collection:
            suffix = "-" + str(i)
            ret = base_id + suffix
            i += 1
        return ret

    def pytest_generate_tests(self, metafunc):
        if 'yml_test_case' in metafunc.fixturenames:
            entries = []
            entry_ids = []
            entry_set = set()

            for filename, _ in zip(*files_and_ids()):
                with open(os.path.join(__location__, filename), 'r', encoding='utf-8') as infile:
                    data = yaml.load(infile, OrderedDictYAMLLoader)

                last_expected = None
                for string, expected in reversed(list(data.items())):
                    if expected is None:
                        data[string] = last_expected
                    else:
                        last_expected = expected

                default = None
                try:
                    default = data['__default__']
                    del data['__default__']
                except KeyError:
                    pass

                for string, expected in data.items():
                    TestYml.set_default(expected, default)
                    string = TestYml.fix_encoding(string, expected)

                    entries.append((filename, string, expected))
                    unique_id = self._get_unique_id(entry_set, '[' + filename + '] ' + str(string))
                    entry_set.add(unique_id)
                    entry_ids.append(unique_id)

            metafunc.parametrize('yml_test_case', entries, ids=entry_ids)

    @staticmethod
    def set_default(expected, default):
        if default:
            for k, v in default.items():
                if k not in expected:
                    expected[k] = v

    @classmethod
    def fix_encoding(cls, string, expected):
        if six.PY2:
            if isinstance(string, six.text_type):
                string = string.encode('utf-8')
            converts = []
            for k, v in expected.items():
                if isinstance(v, six.text_type):
                    v = v.encode('utf-8')
                    converts.append((k, v))
            for k, v in converts:
                expected[k] = v
        if not isinstance(string, str):
            string = str(string)
        return string

    def test_entry(self, yml_test_case):
        filename, string, expected = yml_test_case
        result = self.check_data(filename, string, expected)
        assert not result.error

    def check_data(self, filename, string, expected):
        entry = self.check(string, expected)
        if entry.ok:
            logger.debug('[%s] %s', filename, entry)
        elif entry.warning:
            logger.warning('[%s] %s', filename, entry)
        elif entry.error:
            logger.error('[%s] %s', filename, entry)
            for line in entry.details:
                logger.error('[%s] %s', filename, ' ' * 4 + line)
        return entry

    def check(self, string, expected):
        negates, global_, string = self.parse_token_options(string)

        options = expected.get('options')
        if options is None:
            options = {}
        if not isinstance(options, dict):
            options = parse_options(options)
        try:
            result = guessit(string, options)
        except Exception as exc:
            logger.error('[%s] Exception: %s', string, exc)
            raise exc

        entry = EntryResult(string, negates)

        if global_:
            self.check_global(string, result, entry)

        self.check_expected(result, expected, entry)

        return entry

    def parse_token_options(self, string):
        matches = self.options_re.search(string)
        negates = False
        global_ = False
        if matches:
            string = matches.group(2)
            for opt in matches.group(1):
                if '-' in opt:
                    negates = True
                if '+' in opt:
                    global_ = True
        return negates, global_, string

    def check_global(self, string, result, entry):
        global_span = []
        for result_matches in result.matches.values():
            for result_match in result_matches:
                if not global_span:
                    global_span = list(result_match.span)
                else:
                    if global_span[0] > result_match.span[0]:
                        global_span[0] = result_match.span[0]
                    if global_span[1] < result_match.span[1]:
                        global_span[1] = result_match.span[1]
        if global_span and global_span[1] - global_span[0] < len(string):
            entry.others.append("Match is not global")

    def is_same(self, value, expected):
        values = set(value) if is_iterable(value) else set((value,))
        expecteds = set(expected) if is_iterable(expected) else set((expected,))
        if len(values) != len(expecteds):
            return False
        if isinstance(next(iter(values)), babelfish.Language):
            # pylint: disable=no-member
            expecteds = {babelfish.Language.fromguessit(expected) for expected in expecteds}
        elif isinstance(next(iter(values)), babelfish.Country):
            # pylint: disable=no-member
            expecteds = {babelfish.Country.fromguessit(expected) for expected in expecteds}
        return values == expecteds

    def check_expected(self, result, expected, entry):
        if expected:
            for expected_key, expected_value in expected.items():
                if expected_key and expected_key != 'options' and expected_value is not None:
                    negates_key, _, result_key = self.parse_token_options(expected_key)
                    if result_key in result.keys():
                        if not self.is_same(result[result_key], expected_value):
                            if negates_key:
                                entry.valid.append((expected_key, expected_value))
                            else:
                                entry.different.append((expected_key, expected_value, result[result_key]))
                        else:
                            if negates_key:
                                entry.different.append((expected_key, expected_value, result[result_key]))
                            else:
                                entry.valid.append((expected_key, expected_value))
                    elif not negates_key:
                        entry.missing.append((expected_key, expected_value))

        for result_key, result_value in result.items():
            if result_key not in expected.keys():
                entry.extra.append((result_key, result_value))
