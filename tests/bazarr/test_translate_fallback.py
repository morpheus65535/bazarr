# coding=utf-8

from types import SimpleNamespace

import pytest

from bazarr.subtitles.tools.translate import fallback
from bazarr.subtitles.tools.translate.fallback import pick_translation_source


def _sub(code2, path=None, forced=False, hi=False, track_id=None, sub_id=1):
    """Build a row shaped like the dicts returned by get_subtitles()."""
    return {
        'id': sub_id,
        'name': f'fake.{code2}.srt',
        'code2': code2,
        'code3': code2,
        'forced': forced,
        'hi': hi,
        'path': path,
        'embedded_track_id': track_id,
        'file_size': 1024,
    }


def test_no_candidates_returns_none():
    assert pick_translation_source([], 'zh', ['en']) is None


def test_target_language_is_never_a_source():
    subs = [_sub('zh', path='/m/foo.zh.srt')]
    assert pick_translation_source(subs, 'zh', []) is None


def test_forced_subtitles_are_never_sources():
    subs = [_sub('en', path='/m/foo.en.srt', forced=True)]
    assert pick_translation_source(subs, 'zh', []) is None


def test_hearing_impaired_subtitles_are_valid_sources():
    subs = [_sub('en', path='/m/foo.en.srt', hi=True)]
    assert pick_translation_source(subs, 'zh', []) is subs[0]


def test_preferred_source_language_wins_in_listed_order():
    subs = [
        _sub('de', path='/m/foo.de.srt', sub_id=1),
        _sub('fr', path='/m/foo.fr.srt', sub_id=2),
        _sub('en', path='/m/foo.en.srt', sub_id=3),
    ]
    chosen = pick_translation_source(subs, 'zh', audio_languages=['de'],
                                     preferred_from=['en', 'fr'])
    assert chosen['code2'] == 'en'

    chosen = pick_translation_source(subs, 'zh', audio_languages=['de'],
                                     preferred_from=['fr'])
    assert chosen['code2'] == 'fr'


def test_audio_language_is_used_when_no_preference_given():
    subs = [
        _sub('de', path='/m/foo.de.srt'),
        _sub('ja', path='/m/foo.ja.srt'),
    ]
    chosen = pick_translation_source(subs, 'zh', audio_languages=['ja'])
    assert chosen['code2'] == 'ja'


def test_any_language_used_as_last_resort():
    subs = [_sub('ko', path='/m/foo.ko.srt')]
    chosen = pick_translation_source(subs, 'zh', audio_languages=['ja'])
    assert chosen['code2'] == 'ko'


def test_external_file_beats_embedded_track_of_same_language():
    subs = [
        _sub('en', track_id=2, sub_id=1),
        _sub('en', path='/m/foo.en.srt', sub_id=2),
    ]
    chosen = pick_translation_source(subs, 'zh', [])
    assert chosen['path'] == '/m/foo.en.srt'


def test_preferred_external_beats_lower_ranked_external():
    subs = [
        _sub('en', path='/m/foo.en.srt', sub_id=1),
        _sub('fr', path='/m/foo.fr.srt', sub_id=2),
    ]
    chosen = pick_translation_source(subs, 'zh', [], preferred_from=['fr'])
    assert chosen['code2'] == 'fr'


def test_matching_is_case_insensitive():
    subs = [_sub('EN', path='/m/foo.en.srt')]
    chosen = pick_translation_source(subs, 'ZH', ['en'], preferred_from=['EN'])
    assert chosen['code2'] == 'EN'


EPISODE = SimpleNamespace(sonarrEpisodeId=42, sonarrSeriesId=7, profileId=1,
                          missing_subtitles="['zh']", audio_language='[{"code2": "en"}]',
                          path='/tv/foo.mkv', seriesTitle='Foo', imdbId=None, tvdbId=None,
                          season=1, episode=2, title='Bar')


@pytest.fixture
def wanted_episode(mocker):
    mocker.patch.object(fallback.settings.translator, 'auto_translate_from', [])
    mocker.patch.object(fallback, 'database')
    fallback.database.execute.return_value.first.return_value = EPISODE
    mocker.patch.object(fallback, 'path_mappings')
    fallback.path_mappings.path_replace.return_value = '/tv/foo.mkv'
    mocker.patch.object(fallback.os.path, 'isfile', return_value=True)
    mocker.patch.object(fallback, 'get_audio_profile_languages', return_value=[{'code2': 'en'}])
    translate = mocker.patch.object(fallback, 'translate_subtitles_file')
    extract = mocker.patch.object(fallback, 'extract_and_translate_embedded')
    return translate, extract


def test_no_translation_when_profile_has_no_auto_translate(wanted_episode, mocker):
    mocker.patch.object(fallback, 'get_profiles_list', return_value={'profileId': 1,
                                                                     'autoTranslate': None})
    translate, extract = wanted_episode
    fallback.auto_translate_missing(sonarr_episode_id=42)
    translate.assert_not_called()
    extract.assert_not_called()


def test_no_translation_when_media_has_no_profile(wanted_episode, mocker):
    mocker.patch.object(fallback, 'get_profiles_list', return_value=[{'profileId': 1}])
    translate, extract = wanted_episode
    fallback.auto_translate_missing(sonarr_episode_id=42)
    translate.assert_not_called()
    extract.assert_not_called()


def test_external_source_is_translated_when_profile_enabled(wanted_episode, mocker):
    mocker.patch.object(fallback, 'get_profiles_list', return_value={'profileId': 1,
                                                                     'autoTranslate': 1})
    mocker.patch.object(fallback, 'get_subtitles',
                        return_value=[_sub('en', path='/tv/foo.en.srt', sub_id=3)])
    translate, extract = wanted_episode
    fallback.auto_translate_missing(sonarr_episode_id=42)
    translate.assert_called_once()
    assert translate.call_args.kwargs['source_srt_file'] == '/tv/foo.en.srt'
    assert translate.call_args.kwargs['to_lang'] == 'zh'
    extract.assert_not_called()


def test_embedded_source_is_extracted_then_translated(wanted_episode, mocker):
    mocker.patch.object(fallback, 'get_profiles_list', return_value={'profileId': 1,
                                                                     'autoTranslate': 1})
    mocker.patch.object(fallback, 'get_subtitles',
                        return_value=[_sub('en', track_id=9, sub_id=3)])
    translate, extract = wanted_episode
    fallback.auto_translate_missing(sonarr_episode_id=42)
    extract.assert_called_once()
    assert extract.call_args.kwargs['subtitles_id'] == 3
    translate.assert_not_called()


def test_forced_and_hi_missing_entries_are_not_translated(wanted_episode, mocker):
    mocker.patch.object(fallback, 'get_profiles_list', return_value={'profileId': 1,
                                                                     'autoTranslate': 1})
    fallback.database.execute.return_value.first.return_value = SimpleNamespace(
        **{**EPISODE.__dict__, 'missing_subtitles': "['zh:forced', 'zh:hi']"})
    mocker.patch.object(fallback, 'get_subtitles',
                        return_value=[_sub('en', path='/tv/foo.en.srt', sub_id=3)])
    translate, extract = wanted_episode
    fallback.auto_translate_missing(sonarr_episode_id=42)
    translate.assert_not_called()
    extract.assert_not_called()
