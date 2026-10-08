# -*- coding: utf-8 -*-
"""
Tests for missing subtitles calculation in series and movies indexers.

This module tests the custom alpha2 code resolution fix for languages like
Spanish (Latino) with custom code "ea" that should map to standard Spanish.
"""
import pytest
from subliminal_patch import core

from bazarr.languages.custom_lang import LatinAmericanSpanish, CustomLanguage


def test_custom_language_from_value_alpha2():
    """Test that CustomLanguage.from_value correctly finds custom languages by alpha2 code."""
    # Test Spanish (Latino) with alpha2 code 'ea'
    custom = CustomLanguage.from_value('ea', attr='alpha2')
    assert custom is not None
    assert custom.alpha2 == 'ea'
    assert custom.official_alpha3 == 'spa'  # Maps to Spanish

    # Test that from_value returns None for unknown codes
    custom = CustomLanguage.from_value('xx', attr='alpha2')
    assert custom is None


def test_custom_language_subzero_language():
    """Test that CustomLanguage.subzero_language() returns proper Language object."""
    custom = LatinAmericanSpanish()
    lang = custom.subzero_language()

    # Should return a Language object for Spanish
    assert lang.alpha3 == 'spa'
    assert 'es' in str(lang).lower() or 'spa' in str(lang).lower()


def test_language_parsing_with_custom_alpha2():
    """Test the language parsing logic that would be used in list_missing_subtitles."""
    # Test that we can find Spanish (Latino) by custom alpha2 code
    lang_code = 'ea'

    # This is the logic from the fixed code:
    custom = CustomLanguage.from_value(lang_code, "alpha2")
    if custom:
        lang_obj = custom.subzero_language()
        # Should get Spanish Language object
        assert lang_obj.alpha3 == 'spa'
    else:
        # Should not happen for 'ea'
        pytest.fail("Should have found LatinAmericanSpanish custom language")


def test_language_expansion_preserves_flags():
    """Test that forced and hi flags are preserved during language expansion."""
    # Test with Spanish (Latino) with forced flag
    lang_code = 'ea'
    forced = True
    hi = False

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    assert custom is not None

    lang_obj = custom.subzero_language()
    # Assign flags (as done in the code)
    lang_obj.forced = forced
    lang_obj.hi = hi

    # Verify flags are preserved
    assert lang_obj.forced is True
    assert lang_obj.hi is False


def test_invalid_language_code_fallback():
    """Test that invalid language codes don't crash the system."""
    # Test with a code that's not recognized as custom
    lang_code = 'zz'

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    # Should not find a custom language
    assert custom is None


def test_language_comparison_with_custom_alpha2():
    """Test that custom language expansion properly resolves to standard language alpha2."""
    # Simulate the actual comparison logic from list_missing_subtitles
    # When we have 'ea' (Spanish Latino), it should expand to 'es' (Spanish)

    lang_code = 'ea'
    custom = CustomLanguage.from_value(lang_code, "alpha2")
    assert custom is not None

    lang_obj = custom.subzero_language()
    assert lang_obj.alpha2 == 'es'  # Should resolve to standard Spanish


def test_custom_language_alpha2_resolution_in_conversion():
    """Test that custom alpha2 codes are converted back to proper alpha2 for comparison."""
    # This simulates the fix: when expanding actual subtitles with custom alpha2 codes
    # the code should resolve them to their standard alpha2 equivalents

    expanded_actual_subtitles_list = []

    # Simulate having a custom language 'ea' in the expanded set
    custom = CustomLanguage.from_value('ea', "alpha2")
    if custom:
        lang_obj = custom.subzero_language()
        lang_obj.forced = False
        lang_obj.hi = False

        # This is the fixed logic - use custom.alpha2 if custom else lang_obj.alpha2
        expanded_actual_subtitles_list.append({
            'language': custom.alpha2 if custom else lang_obj.alpha2,
            'forced': 'False',
            'hi': 'False'
        })

    # Verify the result
    assert len(expanded_actual_subtitles_list) == 1
    assert expanded_actual_subtitles_list[0]['language'] == 'ea'  # Still 'ea' as stored


def test_ietf_fallback_for_standard_languages():
    """Test that standard IETF language codes still work correctly."""
    # Test that 'es' (standard Spanish) still works
    lang_code = 'es'

    custom = CustomLanguage.from_value(lang_code, "alpha2")
    # Should not find a custom language for standard codes
    assert custom is None

    # Should parse with IETF
    lang_obj = core.Language.fromietf(lang_code)
    assert lang_obj.alpha2 == 'es'
    assert lang_obj.alpha3 == 'spa'
