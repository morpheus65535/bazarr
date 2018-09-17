#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 the BabelFish authors. All rights reserved.
# Use of this source code is governed by the 3-clause BSD license
# that can be found in the LICENSE file.
#
from __future__ import unicode_literals
import re
import sys
import pickle
from unittest import TestCase, TestSuite, TestLoader, TextTestRunner
from pkg_resources import resource_stream  # @UnresolvedImport
from babelfish import (LANGUAGES, Language, Country, Script, language_converters, country_converters,
    LanguageReverseConverter, LanguageConvertError, LanguageReverseError, CountryReverseError)


if sys.version_info[:2] <= (2, 6):
    _MAX_LENGTH = 80

    def safe_repr(obj, short=False):
        try:
            result = repr(obj)
        except Exception:
            result = object.__repr__(obj)
        if not short or len(result) < _MAX_LENGTH:
            return result
        return result[:_MAX_LENGTH] + ' [truncated]...'

    class _AssertRaisesContext(object):
        """A context manager used to implement TestCase.assertRaises* methods."""

        def __init__(self, expected, test_case, expected_regexp=None):
            self.expected = expected
            self.failureException = test_case.failureException
            self.expected_regexp = expected_regexp

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, tb):
            if exc_type is None:
                try:
                    exc_name = self.expected.__name__
                except AttributeError:
                    exc_name = str(self.expected)
                raise self.failureException(
                    "{0} not raised".format(exc_name))
            if not issubclass(exc_type, self.expected):
                # let unexpected exceptions pass through
                return False
            self.exception = exc_value  # store for later retrieval
            if self.expected_regexp is None:
                return True

            expected_regexp = self.expected_regexp
            if isinstance(expected_regexp, basestring):
                expected_regexp = re.compile(expected_regexp)
            if not expected_regexp.search(str(exc_value)):
                raise self.failureException('"%s" does not match "%s"' %
                         (expected_regexp.pattern, str(exc_value)))
            return True

    class _Py26FixTestCase(object):
        def assertIsNone(self, obj, msg=None):
            """Same as self.assertTrue(obj is None), with a nicer default message."""
            if obj is not None:
                standardMsg = '%s is not None' % (safe_repr(obj),)
                self.fail(self._formatMessage(msg, standardMsg))

        def assertIsNotNone(self, obj, msg=None):
            """Included for symmetry with assertIsNone."""
            if obj is None:
                standardMsg = 'unexpectedly None'
                self.fail(self._formatMessage(msg, standardMsg))

        def assertIn(self, member, container, msg=None):
            """Just like self.assertTrue(a in b), but with a nicer default message."""
            if member not in container:
                standardMsg = '%s not found in %s' % (safe_repr(member),
                                                      safe_repr(container))
                self.fail(self._formatMessage(msg, standardMsg))

        def assertNotIn(self, member, container, msg=None):
            """Just like self.assertTrue(a not in b), but with a nicer default message."""
            if member in container:
                standardMsg = '%s unexpectedly found in %s' % (safe_repr(member),
                                                            safe_repr(container))
                self.fail(self._formatMessage(msg, standardMsg))

        def assertIs(self, expr1, expr2, msg=None):
            """Just like self.assertTrue(a is b), but with a nicer default message."""
            if expr1 is not expr2:
                standardMsg = '%s is not %s' % (safe_repr(expr1),
                                                 safe_repr(expr2))
                self.fail(self._formatMessage(msg, standardMsg))

        def assertIsNot(self, expr1, expr2, msg=None):
            """Just like self.assertTrue(a is not b), but with a nicer default message."""
            if expr1 is expr2:
                standardMsg = 'unexpectedly identical: %s' % (safe_repr(expr1),)
                self.fail(self._formatMessage(msg, standardMsg))

else:
    class _Py26FixTestCase(object):
        pass


class TestScript(TestCase, _Py26FixTestCase):
    def test_wrong_script(self):
        self.assertRaises(ValueError, lambda: Script('Azer'))

    def test_eq(self):
        self.assertEqual(Script('Latn'), Script('Latn'))

    def test_ne(self):
        self.assertNotEqual(Script('Cyrl'), Script('Latn'))

    def test_hash(self):
        self.assertEqual(hash(Script('Hira')), hash('Hira'))

    def test_pickle(self):
        self.assertEqual(pickle.loads(pickle.dumps(Script('Latn'))), Script('Latn'))


class TestCountry(TestCase, _Py26FixTestCase):
    def test_wrong_country(self):
        self.assertRaises(ValueError, lambda: Country('ZZ'))

    def test_eq(self):
        self.assertEqual(Country('US'), Country('US'))

    def test_ne(self):
        self.assertNotEqual(Country('GB'), Country('US'))
        self.assertIsNotNone(Country('US'))

    def test_hash(self):
        self.assertEqual(hash(Country('US')), hash('US'))

    def test_pickle(self):
        for country in [Country('GB'), Country('US')]:
            self.assertEqual(pickle.loads(pickle.dumps(country)), country)

    def test_converter_name(self):
        self.assertEqual(Country('US').name, 'UNITED STATES')
        self.assertEqual(Country.fromname('UNITED STATES'), Country('US'))
        self.assertEqual(Country.fromcode('UNITED STATES', 'name'), Country('US'))
        self.assertRaises(CountryReverseError, lambda: Country.fromname('ZZZZZ'))
        self.assertEqual(len(country_converters['name'].codes), 249)


class TestLanguage(TestCase, _Py26FixTestCase):
    def test_languages(self):
        self.assertEqual(len(LANGUAGES), 7874)

    def test_wrong_language(self):
        self.assertRaises(ValueError, lambda: Language('zzz'))

    def test_unknown_language(self):
        self.assertEqual(Language('zzzz', unknown='und'), Language('und'))

    def test_converter_alpha2(self):
        self.assertEqual(Language('eng').alpha2, 'en')
        self.assertEqual(Language.fromalpha2('en'), Language('eng'))
        self.assertEqual(Language.fromcode('en', 'alpha2'), Language('eng'))
        self.assertRaises(LanguageReverseError, lambda: Language.fromalpha2('zz'))
        self.assertRaises(LanguageConvertError, lambda: Language('aaa').alpha2)
        self.assertEqual(len(language_converters['alpha2'].codes), 184)

    def test_converter_alpha3b(self):
        self.assertEqual(Language('fra').alpha3b, 'fre')
        self.assertEqual(Language.fromalpha3b('fre'), Language('fra'))
        self.assertEqual(Language.fromcode('fre', 'alpha3b'), Language('fra'))
        self.assertRaises(LanguageReverseError, lambda: Language.fromalpha3b('zzz'))
        self.assertRaises(LanguageConvertError, lambda: Language('aaa').alpha3b)
        self.assertEqual(len(language_converters['alpha3b'].codes), 418)

    def test_converter_alpha3t(self):
        self.assertEqual(Language('fra').alpha3t, 'fra')
        self.assertEqual(Language.fromalpha3t('fra'), Language('fra'))
        self.assertEqual(Language.fromcode('fra', 'alpha3t'), Language('fra'))
        self.assertRaises(LanguageReverseError, lambda: Language.fromalpha3t('zzz'))
        self.assertRaises(LanguageConvertError, lambda: Language('aaa').alpha3t)
        self.assertEqual(len(language_converters['alpha3t'].codes), 418)

    def test_converter_name(self):
        self.assertEqual(Language('eng').name, 'English')
        self.assertEqual(Language.fromname('English'), Language('eng'))
        self.assertEqual(Language.fromcode('English', 'name'), Language('eng'))
        self.assertRaises(LanguageReverseError, lambda: Language.fromname('Zzzzzzzzz'))
        self.assertEqual(len(language_converters['name'].codes), 7874)

    def test_converter_scope(self):
        self.assertEqual(language_converters['scope'].codes, set(['I', 'S', 'M']))
        self.assertEqual(Language('eng').scope, 'individual')
        self.assertEqual(Language('und').scope, 'special')

    def test_converter_type(self):
        self.assertEqual(language_converters['type'].codes, set(['A', 'C', 'E', 'H', 'L', 'S']))
        self.assertEqual(Language('eng').type, 'living')
        self.assertEqual(Language('und').type, 'special')

    def test_converter_opensubtitles(self):
        self.assertEqual(Language('fra').opensubtitles, Language('fra').alpha3b)
        self.assertEqual(Language('por', 'BR').opensubtitles, 'pob')
        self.assertEqual(Language.fromopensubtitles('fre'), Language('fra'))
        self.assertEqual(Language.fromopensubtitles('pob'), Language('por', 'BR'))
        self.assertEqual(Language.fromopensubtitles('pb'), Language('por', 'BR'))
        # Montenegrin is not recognized as an ISO language (yet?) but for now it is
        # unofficially accepted as Serbian from Montenegro
        self.assertEqual(Language.fromopensubtitles('mne'), Language('srp', 'ME'))
        self.assertEqual(Language.fromcode('pob', 'opensubtitles'), Language('por', 'BR'))
        self.assertRaises(LanguageReverseError, lambda: Language.fromopensubtitles('zzz'))
        self.assertRaises(LanguageConvertError, lambda: Language('aaa').opensubtitles)
        self.assertEqual(len(language_converters['opensubtitles'].codes), 606)

        # test with all the LANGUAGES from the opensubtitles api
        # downloaded from: http://www.opensubtitles.org/addons/export_languages.php
        f = resource_stream('babelfish', 'data/opensubtitles_languages.txt')
        f.readline()
        for l in f:
            idlang, alpha2, _, upload_enabled, web_enabled = l.decode('utf-8').strip().split('\t')
            if not int(upload_enabled) and not int(web_enabled):
                # do not test LANGUAGES that are too esoteric / not widely available
                continue
            self.assertEqual(Language.fromopensubtitles(idlang).opensubtitles, idlang)
            if alpha2:
                self.assertEqual(Language.fromopensubtitles(idlang), Language.fromopensubtitles(alpha2))
        f.close()

    def test_fromietf_country_script(self):
        language = Language.fromietf('fra-FR-Latn')
        self.assertEqual(language.alpha3, 'fra')
        self.assertEqual(language.country, Country('FR'))
        self.assertEqual(language.script, Script('Latn'))

    def test_fromietf_country_no_script(self):
        language = Language.fromietf('fra-FR')
        self.assertEqual(language.alpha3, 'fra')
        self.assertEqual(language.country, Country('FR'))
        self.assertIsNone(language.script)

    def test_fromietf_no_country_no_script(self):
        language = Language.fromietf('fra-FR')
        self.assertEqual(language.alpha3, 'fra')
        self.assertEqual(language.country, Country('FR'))
        self.assertIsNone(language.script)

    def test_fromietf_no_country_script(self):
        language = Language.fromietf('fra-Latn')
        self.assertEqual(language.alpha3, 'fra')
        self.assertIsNone(language.country)
        self.assertEqual(language.script, Script('Latn'))

    def test_fromietf_alpha2_language(self):
        language = Language.fromietf('fr-Latn')
        self.assertEqual(language.alpha3, 'fra')
        self.assertIsNone(language.country)
        self.assertEqual(language.script, Script('Latn'))

    def test_fromietf_wrong_language(self):
        self.assertRaises(ValueError, lambda: Language.fromietf('xyz-FR'))

    def test_fromietf_wrong_country(self):
        self.assertRaises(ValueError, lambda: Language.fromietf('fra-YZ'))

    def test_fromietf_wrong_script(self):
        self.assertRaises(ValueError, lambda: Language.fromietf('fra-FR-Wxyz'))

    def test_eq(self):
        self.assertEqual(Language('eng'), Language('eng'))

    def test_ne(self):
        self.assertNotEqual(Language('fra'), Language('eng'))
        self.assertIsNotNone(Language('fra'))

    def test_nonzero(self):
        self.assertFalse(bool(Language('und')))
        self.assertTrue(bool(Language('eng')))

    def test_language_hasattr(self):
        self.assertTrue(hasattr(Language('fra'), 'alpha3'))
        self.assertTrue(hasattr(Language('fra'), 'alpha2'))
        self.assertFalse(hasattr(Language('bej'), 'alpha2'))

    def test_country_hasattr(self):
        self.assertTrue(hasattr(Country('US'), 'name'))
        self.assertTrue(hasattr(Country('FR'), 'alpha2'))
        self.assertFalse(hasattr(Country('BE'), 'none'))

    def test_country(self):
        self.assertEqual(Language('por', 'BR').country, Country('BR'))
        self.assertEqual(Language('eng', Country('US')).country, Country('US'))

    def test_eq_with_country(self):
        self.assertEqual(Language('eng', 'US'), Language('eng', Country('US')))

    def test_ne_with_country(self):
        self.assertNotEqual(Language('eng', 'US'), Language('eng', Country('GB')))

    def test_script(self):
        self.assertEqual(Language('srp', script='Latn').script, Script('Latn'))
        self.assertEqual(Language('srp', script=Script('Cyrl')).script, Script('Cyrl'))

    def test_eq_with_script(self):
        self.assertEqual(Language('srp', script='Latn'), Language('srp', script=Script('Latn')))

    def test_ne_with_script(self):
        self.assertNotEqual(Language('srp', script='Latn'), Language('srp', script=Script('Cyrl')))

    def test_eq_with_country_and_script(self):
        self.assertEqual(Language('srp', 'SR', 'Latn'), Language('srp', Country('SR'), Script('Latn')))

    def test_ne_with_country_and_script(self):
        self.assertNotEqual(Language('srp', 'SR', 'Latn'), Language('srp', Country('SR'), Script('Cyrl')))

    def test_hash(self):
        self.assertEqual(hash(Language('fra')), hash('fr'))
        self.assertEqual(hash(Language('ace')), hash('ace'))
        self.assertEqual(hash(Language('por', 'BR')), hash('pt-BR'))
        self.assertEqual(hash(Language('srp', script='Cyrl')), hash('sr-Cyrl'))
        self.assertEqual(hash(Language('eng', 'US', 'Latn')), hash('en-US-Latn'))

    def test_pickle(self):
        for lang in [Language('fra'),
                     Language('eng', 'US'),
                     Language('srp', script='Latn'),
                     Language('eng', 'US', 'Latn')]:
            self.assertEqual(pickle.loads(pickle.dumps(lang)), lang)

    def test_str(self):
        self.assertEqual(Language.fromietf(str(Language('eng', 'US', 'Latn'))), Language('eng', 'US', 'Latn'))
        self.assertEqual(Language.fromietf(str(Language('fra', 'FR'))), Language('fra', 'FR'))
        self.assertEqual(Language.fromietf(str(Language('bel'))), Language('bel'))

    def test_register_converter(self):
        class TestConverter(LanguageReverseConverter):
            def __init__(self):
                self.to_test = {'fra': 'test1', 'eng': 'test2'}
                self.from_test = {'test1': 'fra', 'test2': 'eng'}

            def convert(self, alpha3, country=None, script=None):
                if alpha3 not in self.to_test:
                    raise LanguageConvertError(alpha3, country, script)
                return self.to_test[alpha3]

            def reverse(self, test):
                if test not in self.from_test:
                    raise LanguageReverseError(test)
                return (self.from_test[test], None)
        language = Language('fra')
        self.assertFalse(hasattr(language, 'test'))
        language_converters['test'] = TestConverter()
        self.assertTrue(hasattr(language, 'test'))
        self.assertIn('test', language_converters)
        self.assertEqual(Language('fra').test, 'test1')
        self.assertEqual(Language.fromtest('test2').alpha3, 'eng')
        del language_converters['test']
        self.assertNotIn('test', language_converters)
        self.assertRaises(KeyError, lambda: Language.fromtest('test1'))
        self.assertRaises(AttributeError, lambda: Language('fra').test)


def suite():
    suite = TestSuite()
    suite.addTest(TestLoader().loadTestsFromTestCase(TestScript))
    suite.addTest(TestLoader().loadTestsFromTestCase(TestCountry))
    suite.addTest(TestLoader().loadTestsFromTestCase(TestLanguage))
    return suite


if __name__ == '__main__':
    TextTestRunner().run(suite())
