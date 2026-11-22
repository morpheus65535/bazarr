# -*- coding: utf-8 -*-
import io
import zipfile

import pytest
from babelfish import language_converters
from subzero.language import Language
from subliminal.exceptions import DownloadLimitExceeded, ProviderError
from subliminal.video import Episode, Movie
from subliminal_patch.exceptions import TooManyRequests

from subliminal_patch.converters.subhd import SubhdConverter
from subliminal_patch.providers.subhd import (
    SubhdProvider,
    SubhdSubtitle,
    _extract_subtitle_from_archive,
    _has_keyword,
)


class MockResponse:
    def __init__(self, content=b"", json_data=None, status_code=200):
        self.content = content if isinstance(content, bytes) else content.encode("utf-8")
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP Error {self.status_code}")


class MockSession:
    def __init__(self):
        self.headers = {}
        self.get_responses = {}
        self.post_responses = {}
        self.history = []

    def get(self, url, **kwargs):
        self.history.append(("GET", url, kwargs))
        if url in self.get_responses:
            return self.get_responses[url]
        for key, resp in self.get_responses.items():
            if key in url:
                return resp
        return MockResponse(b"<html></html>")

    def post(self, url, **kwargs):
        self.history.append(("POST", url, kwargs))
        if url in self.post_responses:
            return self.post_responses[url]
        for key, resp in self.post_responses.items():
            if key in url:
                return resp
        return MockResponse(json_data={"success": True})

    def close(self):
        pass


MOCK_SEARCH_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="bg-white shadow-sm rounded-3 mb-4">
  <div class="row">
    <div class="col-lg-10">
      <div class="pt-3 pe-3 pb-2 ps-3 ps-lg-0 position-relative">
        <div class="clearfix">
          <div class="float-start f16 fw-bold">
            <a class="link-dark align-middle" href='/a/RH84Ye'>母狮 第三季 (2026)</a>
          </div>
          <div class="view-text text-secondary">
            <a href='/a/RH84Ye' class='link-dark'>
              Special.Ops.Lioness.S03E07.1080p.10bit.WEBRip.6CH.x265.HEVC-PSA.Bilingual.en-zh
            </a>
          </div>
          <div class="text-truncate py-2 f11">
            <span class="rounded p-1 me-1 text-white">AI校对</span>
            <span class="p-1 fw-bold">双语</span>
            <span class="p-1 fw-bold">简体</span><span class="p-1 fw-bold">英语</span>
            <span class="p-1 text-secondary">SRT</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<div class="bg-white shadow-sm rounded-3 mb-4">
  <div class="row">
    <div class="col-lg-10">
      <div class="pt-3 pe-3 pb-2 ps-3 ps-lg-0 position-relative">
        <div class="clearfix">
          <div class="float-start f16 fw-bold">
            <a class="link-dark align-middle" href='/a/bqXCxZ'>母狮 第三季</a>
          </div>
          <div class="view-text text-secondary">
            <a href='/a/bqXCxZ' class='link-dark'>
              Lioness.S03E07.1080p.ChatGPT.繁體
            </a>
          </div>
          <div class="text-truncate py-2 f11">
            <span class="p-1 fw-bold">繁体</span>
            <span class="p-1 text-secondary">ASS</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""


def test_subhd_converter():
    converter = SubhdConverter()
    assert converter.convert('zho', 'CN') == 'chs'
    assert converter.convert('zho', 'TW') == 'cht'
    assert converter.convert('eng') == 'eng'
    assert converter.reverse('简体') == ('zho', 'CN', None)
    assert converter.reverse('繁体') == ('zho', 'TW', None)
    assert converter.reverse('双语') == ('zho', 'CN', None)
    assert converter.reverse('英语') == ('eng',)


def test_subhd_parse_search_page():
    provider = SubhdProvider()
    requested_langs = {Language('zho', 'CN'), Language('zho', 'TW')}
    subs = provider._parse_search_page(MOCK_SEARCH_HTML, requested_langs, default_year=2026)

    assert len(subs) == 2

    sub1 = next(s for s in subs if s.sid == 'RH84Ye')
    assert sub1.page_link == 'https://subhd.tv/a/RH84Ye'
    assert sub1.language == Language('zho', 'CN')
    assert sub1.year == 2026
    assert 'Special.Ops.Lioness.S03E07' in sub1.version

    sub2 = next(s for s in subs if s.sid == 'bqXCxZ')
    assert sub2.page_link == 'https://subhd.tv/a/bqXCxZ'
    assert sub2.language == Language('zho', 'TW')
    assert 'Lioness.S03E07' in sub2.version


def test_subhd_list_subtitles_episode():
    provider = SubhdProvider()
    provider.session = MockSession()
    provider.session.get_responses['/search/'] = MockResponse(MOCK_SEARCH_HTML)

    episode = Episode(
        name='Special.Ops.Lioness.S03E07.mkv',
        series='Special Ops: Lioness',
        season=3,
        episode=7,
        year=2026,
    )
    episode.alternative_series = ['Lioness']

    requested_langs = {Language('zho', 'CN')}
    subs = provider.list_subtitles(episode, requested_langs)

    assert len(subs) >= 1
    sub = subs[0]
    matches = sub.get_matches(episode)
    assert 'season' in matches
    assert 'episode' in matches


def test_subhd_download_subtitle_direct_srt():
    provider = SubhdProvider()
    provider.session = MockSession()

    sid = 'RH84Ye'
    provider.session.get_responses[f'/a/{sid}'] = MockResponse(b"<html>detail page</html>")
    provider.session.post_responses['/api/sub/prepare-download'] = MockResponse(
        json_data={'success': True, 'url': f'/down/{sid}'}
    )
    provider.session.get_responses[f'/down/{sid}'] = MockResponse(b"<html>down page</html>")
    provider.session.post_responses['/api/sub/down'] = MockResponse(
        json_data={'success': True, 'pass': True, 'url': 'https://dlus.subhd.me/sub.srt'}
    )
    provider.session.get_responses['https://dlus.subhd.me/sub.srt'] = MockResponse(
        b"1\r\n00:00:01,000 --> 00:00:04,000\r\nHello SubHD\r\n"
    )

    sub = SubhdSubtitle(
        language=Language('zho', 'CN'),
        page_link=f'https://subhd.tv/a/{sid}',
        sid=sid,
        version='Special.Ops.Lioness.S03E07',
    )

    provider.download_subtitle(sub)

    assert sub.content is not None
    assert b"Hello SubHD" in sub.content


def test_subhd_download_subtitle_zip_archive_selection():
    provider = SubhdProvider()
    provider.session = MockSession()

    # Create zip with simplified and traditional files, plus different episode
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w') as zf:
        zf.writestr('Special.Ops.Lioness.S03E07.1080p.简英.ass', b'[Script Info]\nTitle: Simplified E07')
        zf.writestr('Special.Ops.Lioness.S03E07.1080p.繁英.ass', b'[Script Info]\nTitle: Traditional E07')
        zf.writestr('Special.Ops.Lioness.S03E08.1080p.简英.ass', b'[Script Info]\nTitle: Simplified E08')

    sid = 'zipsub123'
    provider.session.get_responses[f'/a/{sid}'] = MockResponse(b"<html>detail</html>")
    provider.session.post_responses['/api/sub/prepare-download'] = MockResponse(
        json_data={'success': True, 'url': f'/down/{sid}'}
    )
    provider.session.get_responses[f'/down/{sid}'] = MockResponse(b"<html>down</html>")
    provider.session.post_responses['/api/sub/down'] = MockResponse(
        json_data={'success': True, 'pass': True, 'url': 'https://dlus.subhd.me/sub.zip'}
    )
    provider.session.get_responses['https://dlus.subhd.me/sub.zip'] = MockResponse(zip_buf.getvalue())

    episode = Episode(
        name='Special.Ops.Lioness.S03E07.mkv',
        series='Special Ops: Lioness',
        season=3,
        episode=7,
    )

    # Test simplified extraction
    sub_chs = SubhdSubtitle(
        language=Language('zho', 'CN'),
        page_link=f'https://subhd.tv/a/{sid}',
        sid=sid,
        version='Special.Ops.Lioness.S03E07',
    )
    sub_chs.video = episode

    provider.download_subtitle(sub_chs)
    assert sub_chs.content is not None
    assert b"Title: Simplified E07" in sub_chs.content

    # Test traditional extraction
    sub_cht = SubhdSubtitle(
        language=Language('zho', 'TW'),
        page_link=f'https://subhd.tv/a/{sid}',
        sid=sid,
        version='Special.Ops.Lioness.S03E07',
    )
    sub_cht.video = episode

    provider.download_subtitle(sub_cht)
    assert sub_cht.content is not None
    assert b"Title: Traditional E07" in sub_cht.content



class FailingSession(MockSession):
    """Session whose GET requests to downloaded file hosts fail with a network error."""

    def get(self, url, **kwargs):
        if 'dlus.subhd.me' in url:
            raise ConnectionError('simulated network failure')
        return super().get(url, **kwargs)


def test_subhd_query_rate_limited_raises_too_many_requests():
    provider = SubhdProvider()
    provider.session = MockSession()
    provider.session.get_responses['/search/'] = MockResponse(b'', status_code=429)

    with pytest.raises(TooManyRequests):
        provider.query('Lioness', {Language('zho', 'CN')})


def test_subhd_query_connection_error_returns_empty():
    provider = SubhdProvider()
    provider.session = MockSession()

    def failing_get(url, **kwargs):
        raise ConnectionError('simulated network failure')

    provider.session.get = failing_get
    assert provider.query('Lioness', {Language('zho', 'CN')}) == []


def test_subhd_download_rate_limited_raises_download_limit():
    provider = SubhdProvider()
    provider.session = MockSession()
    sid = 'limitsub'
    provider.session.post_responses['/api/sub/prepare-download'] = MockResponse(b'', status_code=429)

    sub = SubhdSubtitle(
        language=Language('zho', 'CN'),
        page_link=f'https://subhd.tv/a/{sid}',
        sid=sid,
        version='Lioness.S03E07',
    )

    with pytest.raises(DownloadLimitExceeded):
        provider.download_subtitle(sub)
    assert sub.content is None


def test_subhd_download_network_error_is_swallowed():
    provider = SubhdProvider()
    provider.session = FailingSession()
    sid = 'netfail'
    provider.session.post_responses['/api/sub/prepare-download'] = MockResponse(
        json_data={'success': True, 'url': f'/down/{sid}'}
    )
    provider.session.post_responses['/api/sub/down'] = MockResponse(
        json_data={'success': True, 'pass': True, 'url': 'https://dlus.subhd.me/sub.srt'}
    )

    sub = SubhdSubtitle(
        language=Language('zho', 'CN'),
        page_link=f'https://subhd.tv/a/{sid}',
        sid=sid,
        version='Lioness.S03E07',
    )

    provider.download_subtitle(sub)
    assert sub.content is None


def test_has_keyword_uses_token_boundaries():
    assert not _has_keyword('show.s03e07.escape.srt', ['sc'])
    assert not _has_keyword('scrubs.s01e01.srt', ['sc'])
    assert _has_keyword('show.s03e07.sc.srt', ['sc'])
    assert _has_keyword('show.s03e07.gbk.srt', ['gb', 'gbk'])
    assert _has_keyword('show.s03e07.zh-cn.srt', ['zh-cn'])
    assert _has_keyword('show.s03e07.简英.ass', ['简英'])


def test_subhd_episode_hit_skips_season_query():
    provider = SubhdProvider()
    provider.session = MockSession()
    provider.session.get_responses['/search/'] = MockResponse(MOCK_SEARCH_HTML)

    episode = Episode(name='Lioness.S03E07.mkv', series='Lioness', season=3, episode=7)
    provider.list_subtitles(episode, {Language('zho', 'CN')})

    search_urls = [url for method, url, _ in provider.session.history if method == 'GET' and '/search/' in url]
    assert len(search_urls) == 1
    assert 'S03E07' in search_urls[0]


def test_subhd_season_query_runs_when_episode_query_empty():
    provider = SubhdProvider()
    provider.session = MockSession()
    # Insertion order matters: the episode-specific key must be checked before the generic one.
    provider.session.get_responses['S03E07'] = MockResponse(b'<html></html>')
    provider.session.get_responses['/search/'] = MockResponse(MOCK_SEARCH_HTML)

    episode = Episode(name='Lioness.S03E07.mkv', series='Lioness', season=3, episode=7)
    subs = provider.list_subtitles(episode, {Language('zho', 'CN')})

    search_urls = [url for method, url, _ in provider.session.history if method == 'GET' and '/search/' in url]
    assert len(search_urls) == 2
    assert 'S03E07' in search_urls[0]
    assert 'S03E07' not in search_urls[1]
    assert len(subs) >= 1
