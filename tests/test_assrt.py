# -*- coding: utf-8 -*-
import os

from babelfish import language_converters
from subzero.language import Language
import pytest
from vcr import VCR
from urlparse import urlparse, parse_qs
from urllib import urlencode

from subliminal_patch.providers.assrt import AssrtSubtitle, AssrtProvider, \
language_contains, search_language_in_list, supported_languages


def remove_auth_token(request):
    parsed_uri = urlparse(request.uri)
    parsed_query = parse_qs(parsed_uri.query)
    if 'token' in parsed_query:
        parsed_query['token'] = 'SECRET'
    parsed_uri = parsed_uri._replace(query=urlencode(parsed_query))
    request.uri = parsed_uri.geturl()
    return request


vcr = VCR(path_transformer=lambda path: path + '.yaml',
          before_record_request=remove_auth_token,
          record_mode=os.environ.get('VCR_RECORD_MODE', 'once'),
          match_on=['method', 'scheme', 'host', 'port', 'path', 'body'],
          cassette_library_dir=os.path.realpath(os.path.join('cassettes', 'assrt')))


TOKEN=os.environ.get('ASSRT_TOKEN', 'NO_TOKEN_PROVIDED')


def test_supported_languages():
    assert set(supported_languages) == set([('zho', None, None),
                                            ('eng', None, None),
                                            ('zho', None, 'Hans'),
                                            ('zho', None, 'Hant')])


def test_language_contains():
    assert language_contains(Language('zho'), Language('zho'))
    assert language_contains(Language('zho', 'TW', None), Language('zho'))
    assert language_contains(Language('zho', 'CN', None), Language('zho'))
    assert language_contains(Language('zho', None, 'Hant'), Language('zho'))
    assert language_contains(Language('zho', None, 'Hans'), Language('zho'))
    assert language_contains(Language('zho', 'TW', 'Hant'), Language('zho'))
    assert language_contains(Language('zho', 'CN', 'Hans'), Language('zho'))
    assert language_contains(Language('zho', None, 'Hant'), Language('zho', None, 'Hant'))
    assert language_contains(Language('zho', None, 'Hans'), Language('zho', None, 'Hans'))


def test_search_language_in_list():
    assert search_language_in_list(Language('zho', None, 'Hant'), [Language('zho', None, 'Hant')])
    assert search_language_in_list(Language('zho', None, 'Hans'), [Language('zho', None, 'Hans')])
    assert search_language_in_list(Language('zho', None, 'Hant'), [Language('zho')])
    assert search_language_in_list(Language('zho', None, 'Hans'), [Language('zho')])
    assert search_language_in_list(Language('zho', None, 'Hant'), [Language('eng'), Language('zho')])
    assert not search_language_in_list(Language('zho', None, 'Hans'), [Language('zho', None, 'Hant')])
    assert search_language_in_list(Language('zho', None, 'Hans'), [Language('zho', None, 'Hant'), Language('zho')])


def test_get_matches_exact_movie_name(movies):
    subtitle = AssrtSubtitle(Language('zho'), 253629,
                             'man.of.steel.2013.720p.bluray.x264-felony.mkv',
                             None, None)
    matches = subtitle.get_matches(movies['man_of_steel'])
    assert matches == {'title', 'format', 'release_group', 'year',
                       'video_codec', 'resolution'}


def test_get_matches_movie_name(movies):
    subtitle = AssrtSubtitle(Language('zho'), 618185,
                             'Man.Of.Steel.2013.BluRay.720p.x264.AC3.2Audios-CMCT',
                             None, None)
    matches = subtitle.get_matches(movies['man_of_steel'])
    assert matches == {'title', 'format', 'year', 'video_codec', 'resolution'}


@pytest.mark.converter
def test_converter_convert_alpha3():
    assert language_converters['assrt'].convert('zho', None, 'Hans') == 'chi'
    assert language_converters['assrt'].convert('zho', None, 'Hant') == 'zht'
    assert language_converters['assrt'].convert('eng') == 'eng'


@pytest.mark.converter
def test_converter_reverse():
    assert language_converters['assrt'].reverse('chi') == ('zho', None, 'Hans')
    assert language_converters['assrt'].reverse('zht') == ('zho', None, 'Hant')
    assert language_converters['assrt'].reverse(u'簡體') == ('zho', None, 'Hans')
    assert language_converters['assrt'].reverse(u'繁體') == ('zho', None, 'Hant')
    assert language_converters['assrt'].reverse(u'简体') == ('zho', None, 'Hans')
    assert language_converters['assrt'].reverse(u'繁体') == ('zho', None, 'Hant')


@pytest.mark.integration
@vcr.use_cassette
def test_query_movie_zh_Hans(movies):
    languages = [Language('zho', None, 'Hant')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.query(languages, video)
        assert len(subtitles) == 8


@pytest.mark.integration
@vcr.use_cassette
def test_query_movie_zh_Hant(movies):
    languages = [Language('zho', None, 'Hans')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.query(languages, video)
        assert len(subtitles) == 8


@pytest.mark.integration
@vcr.use_cassette
def test_query_movie_zh(movies):
    languages = [Language('zho')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.query(languages, video)
        assert len(subtitles) == 16


@pytest.mark.integration
@vcr.use_cassette
def test_query_episode(episodes):
    video = episodes['bbt_s07e05']
    languages = [Language('zho', None, 'Hant'), Language('zho', None, 'Hans')]
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.query(languages, video)
        assert len(subtitles) == 11


@pytest.mark.integration
@vcr.use_cassette
def test_query_list_subtitles(movies):
    languages = [Language('zho', None, 'Hant'), Language('zho', None, 'Hans')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.list_subtitles(video, languages)
        assert len(subtitles) == 16


@pytest.mark.integration
@vcr.use_cassette
def test_download_subtitle(movies):
    languages = [Language('zho', None, 'Hant')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.list_subtitles(video, languages)
        provider.download_subtitle(subtitles[0])
        assert subtitles[0].content is not None
        assert subtitles[0].language == Language('zho', None, 'Hant')


@pytest.mark.integration
@vcr.use_cassette
def test_download_subtitle_zh(movies):
    languages = [Language('zho')]
    video = movies['man_of_steel']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.list_subtitles(video, languages)
        provider.download_subtitle(subtitles[0])
        assert subtitles[0].content is not None
        assert subtitles[0].language == Language('zho')


@pytest.mark.integration
@vcr.use_cassette
def test_download_episode_subtitle(episodes):
    languages = [Language('zho', None, 'Hant'), Language('zho', None, 'Hans')]
    video = episodes['bbt_s07e05']
    with AssrtProvider(TOKEN) as provider:
        subtitles = provider.list_subtitles(video, languages)
        provider.download_subtitle(subtitles[0])
        assert subtitles[0].content is not None
        assert subtitles[0].language == Language('zho', None, 'Hans')
