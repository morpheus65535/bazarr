# coding=utf-8

from collections.abc import Callable
from typing import Any

from subliminal_patch import core

from constants import HI_EXCLUDED
from languages.custom_lang import CustomLanguage

ANY_CUTOFF = 65535


def get_desired_subtitles(profile_items, matches_audio):
    """Return the {language, forced, hi} entries the profile asks for, after the audio-track options."""
    desired_subtitles = []
    for language in profile_items:
        if not isinstance(language, dict):
            continue
        language_code = language.get('language')
        if not isinstance(language_code, str) or not language_code:
            continue
        if language.get('audio_exclude') == "True":
            if matches_audio(language):
                continue
        if language.get('audio_only_include') == "True":
            if not matches_audio(language):
                continue
        desired_subtitles.append({'language': language_code,
                                  'forced': str(language.get('forced', False)),
                                  'hi': str(language.get('hi', False))})
    return desired_subtitles


def get_actual_subtitles(subtitles):
    """Return the {language, forced, hi} entries for the subtitles already stored for a media item."""
    actual_subtitles = []
    for subtitle in subtitles:
        if not isinstance(subtitle, dict):
            continue
        language_code = subtitle.get('code2')
        if not isinstance(language_code, str) or not language_code:
            continue
        actual_subtitles.append({'language': language_code,
                                 'forced': str(subtitle.get('forced', False)),
                                 'hi': str(subtitle.get('hi', False))})
    return actual_subtitles


def expand_actual_subtitles(actual_subtitles, lang_equals):
    """Expand the actual subtitles with the language equals configuration."""
    # Convert code2 languages to Language objects for expansion
    actual_subtitles_lang_set = set()
    for sub in actual_subtitles:
        try:
            # Check for custom alpha2 codes first
            custom = CustomLanguage.from_value(sub['language'], "alpha2")
            if custom:
                lang_obj = custom.subzero_language()
            else:
                lang_obj = core.Language.fromietf(sub['language'])
            lang_obj.forced = sub['forced'] == 'True'
            lang_obj.hi = sub['hi'] == 'True'
            actual_subtitles_lang_set.add(lang_obj)
        except Exception:
            # If language parsing fails, add as-is
            actual_subtitles_lang_set.add(sub['language'])

    expanded_actual_lang_set = lang_equals.check_set(actual_subtitles_lang_set)

    # Convert expanded languages back to code2 format for comparison
    expanded_actual_subtitles = []
    for lang_obj in expanded_actual_lang_set:
        if isinstance(lang_obj, core.Language):
            # check if lang_obj is a custom language
            custom = CustomLanguage.from_value(lang_obj, "language")
            # append the language to the list with the proper alpha2 code depending on whether it's custom or not
            expanded_actual_subtitles.append({'language': custom.alpha2 if custom else lang_obj.alpha2,
                                              'forced': 'True' if lang_obj.forced else 'False',
                                              'hi': 'True' if lang_obj.hi else 'False'})
    return expanded_actual_subtitles


def get_non_hi_languages(profile_items):
    """
    Languages with a non-HI item in the profile. Built from every item, not one value per language,
    so a normal item and a non-HI item for the same language don't overwrite each other.
    """
    return {item['language'] for item in profile_items
            if isinstance(item, dict) and isinstance(item.get('language'), str)
            and str(item.get('forced', False)) == 'False' and item.get('hi') == HI_EXCLUDED}


def is_cutoff_met(cutoff_items, matches_audio, actual_subtitles, expanded_actual_subtitles, non_hi_languages):
    """Return True when any cutoff item is satisfied by the existing subtitles."""
    for cutoff_temp in cutoff_items or []:
        if not isinstance(cutoff_temp, dict):
            continue
        cutoff_code = cutoff_temp.get('language')
        if not isinstance(cutoff_code, str) or not cutoff_code:
            continue
        cutoff_language = {'language': cutoff_code,
                           'forced': cutoff_temp.get('forced', 'False'),
                           'hi': cutoff_temp.get('hi', 'False')}
        if cutoff_temp.get('audio_only_include') == 'True' and not matches_audio(cutoff_temp):
            # We don't want subs in this language unless it matches
            # the audio. Don't use it to meet the cutoff.
            continue
        elif cutoff_temp.get('audio_exclude') == 'True' and matches_audio(cutoff_temp):
            # The cutoff is met through one of the audio tracks.
            return True
        elif cutoff_language in actual_subtitles:
            return True
        elif cutoff_language in expanded_actual_subtitles:
            # Check against expanded actual subtitles (includes language equals)
            return True
        elif (cutoff_language['hi'] == 'False' and cutoff_language['forced'] == 'False' and
              cutoff_language['language'] not in non_hi_languages and
              {'language': cutoff_language['language'], 'forced': 'False', 'hi': 'True'} in actual_subtitles):
            # HI is considered as good as normal only if the language isn't set to exclude HI
            return True
        elif (cutoff_language['hi'] == HI_EXCLUDED and
              {'language': cutoff_language['language'],
               'forced': cutoff_language['forced'],
               'hi': 'False'} in actual_subtitles):
            # Cutoff is met by non-HI subtitles when HI subtitles are excluded in languages profile
            return True
    return False


def _unsatisfied_entries(desired_subtitles, actual_subtitles, expanded_actual_subtitles, non_hi_languages):
    """Return the desired entries the existing subtitles do not satisfy. The cutoff is not considered here."""
    missing_subtitles_list = []
    for item in desired_subtitles:
        # Check against both actual and expanded actual subtitles
        if item not in actual_subtitles and item not in expanded_actual_subtitles:
            missing_subtitles_list.append(item)

    for item in actual_subtitles:
        if item['hi'] == 'True' and item['forced'] == 'False' and item['language'] not in non_hi_languages:
            # remove missing that have hi subtitles for this language in existing
            # (unless the language is set to exclude HI)
            try:
                missing_subtitles_list.remove({'language': item['language'], 'forced': 'False', 'hi': 'False'})
            except ValueError:
                pass
        elif item['hi'] == 'False' and item['forced'] == 'False' and item['language'] in non_hi_languages:
            # remove explicitely excluded requested hi subtitles and existing hi subtitles
            try:
                missing_subtitles_list.remove({'language': item['language'], 'forced': 'False', 'hi': HI_EXCLUDED})
            except ValueError:
                pass
    return missing_subtitles_list


def _format_missing(missing_subtitles_list):
    """Convert {language, forced, hi} entries to the strings stored for a media item: 'en', 'en:forced', 'en:hi'."""
    missing_subtitles_output_list = []
    for item in missing_subtitles_list:
        lang = item['language']
        if item['forced'] == 'True':
            lang += ':forced'
        elif item['hi'] == 'True':
            lang += ':hi'
        missing_subtitles_output_list.append(lang)
    return missing_subtitles_output_list


def calculate_missing_subtitles(profile_items, cutoff_items, subtitles, matches_audio, lang_equals):
    """
    Return the missing subtitles of one media item for a basic profile.

    profile_items is the profile's raw item list, cutoff_items the items returned by get_profile_cutoff(),
    and subtitles the stored subtitles of the media item. Nothing is missing once the cutoff is met.
    """
    desired_subtitles = get_desired_subtitles(profile_items, matches_audio)
    actual_subtitles = get_actual_subtitles(subtitles)
    expanded_actual_subtitles = expand_actual_subtitles(actual_subtitles, lang_equals)
    non_hi_languages = get_non_hi_languages(profile_items)

    if is_cutoff_met(cutoff_items, matches_audio, actual_subtitles, expanded_actual_subtitles, non_hi_languages):
        return []

    return _format_missing(
        _unsatisfied_entries(desired_subtitles, actual_subtitles, expanded_actual_subtitles, non_hi_languages))


def _item_outcome(item: object, matches_audio: Callable[[dict[str, Any]], bool],
                  actual_subtitles: list[dict[str, str]], expanded_actual_subtitles: list[dict[str, str]],
                  non_hi_languages: set[str]) -> tuple[dict[str, str] | None, bool] | None:
    """
    Return (entry, satisfied) for one item of an enhanced group, or None when the item is not a language item.

    An item dropped by the audio options has no entry. It is satisfied only when audio_exclude removed it because a
    matching audio track is present. An audio_only_include item with no matching audio track is unsatisfied, so a
    cutoff group that holds it is not met.
    """
    if not isinstance(item, dict) or not isinstance(item.get('language'), str) or not item['language']:
        return None

    desired = get_desired_subtitles([item], matches_audio)
    if not desired:
        return None, item.get('audio_exclude') == 'True' and bool(matches_audio(item))

    entry = desired[0]
    satisfied = not _unsatisfied_entries([entry], actual_subtitles, expanded_actual_subtitles, non_hi_languages)
    return entry, satisfied


def calculate_enhanced_missing_subtitles(groups, cutoff, subtitles, matches_audio, lang_equals):
    """
    Return the missing subtitles of one media item for an enhanced profile.

    A group is satisfied when all its items are satisfied (AND) or when one of them is (OR). An item removed by
    audio_exclude because a matching audio track is present is satisfied. An item removed by audio_only_include
    because no audio track matches is not satisfied, and it adds nothing to the missing list. A satisfied group adds
    nothing to the missing list, and an unsatisfied group adds its unsatisfied items. The cutoff is a group id: it is
    met when that group is satisfied. 65535 is met when any group is satisfied, and no cutoff is never met. Once the
    cutoff is met, nothing is missing.
    """
    group_items = [item for group in groups for item in (group.get('items') or [])]
    actual_subtitles = get_actual_subtitles(subtitles)
    expanded_actual_subtitles = expand_actual_subtitles(actual_subtitles, lang_equals)
    non_hi_languages = get_non_hi_languages(group_items)

    satisfied_group_ids = set()
    missing_subtitles_list = []
    for group in groups:
        outcomes = []
        for item in group.get('items') or []:
            outcome = _item_outcome(item, matches_audio, actual_subtitles, expanded_actual_subtitles,
                                    non_hi_languages)
            if outcome is not None:
                outcomes.append(outcome)
        if not outcomes:
            satisfied_group_ids.add(group.get('id'))
            continue

        satisfied_flags = [satisfied for _, satisfied in outcomes]
        if (any(satisfied_flags) if group.get('operator') == 'OR' else all(satisfied_flags)):
            satisfied_group_ids.add(group.get('id'))
            continue

        for entry, satisfied in outcomes:
            if entry is not None and not satisfied and entry not in missing_subtitles_list:
                missing_subtitles_list.append(entry)

    if not cutoff:
        cutoff_met = False
    elif cutoff == ANY_CUTOFF:
        cutoff_met = bool(satisfied_group_ids)
    else:
        cutoff_met = cutoff in satisfied_group_ids

    if cutoff_met:
        return []
    return _format_missing(missing_subtitles_list)
