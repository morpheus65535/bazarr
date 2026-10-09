from subzero.language import Language
from requests import Session
from subliminal.video import Movie

from subliminal_patch.providers.greeksubs import GreekSubsProvider
from subliminal_patch.providers.greeksubs import GreekSubsSubtitle


REFERER = "https://greeksubs.net/en/view/tt0479997"
STALE_DOWNLOAD_LINK = "https://greeksubs.net/dll/subtitle-id/0/stale-token"
FRESH_DOWNLOAD_LINK = "https://greeksubs.net/dll/subtitle-id/0/fresh-token"


def test_list_subtitles_parses_current_table_markup(requests_mock):
    requests_mock.get(
        REFERER,
        text=(
            '<input type="hidden" value="fresh-token" id="secCode">'
            '<table id="elSub"><tbody><tr>'
            '<td>1</td><td><img src="/resources/lang/greek.jpg" alt="el"></td><span>'
            '<td></td><td></td><td><button onclick="downloadMe(\'subtitle-id\')">Download</button></td>'
            '<td>64</td><td>Season-of-the-Witch-2011-1080p-bluray-x264-blow</td>'
            '<td><img class="userProfileImgN"><div class="userNameBox">WhiteAngel</div></td>'
            '</span></tr></tbody></table>'
        ),
    )
    movie = Movie(
        "Season.of.the.Witch.2011.1080p.BluRay.x264.mkv",
        "Season of the Witch",
        year=2011,
        imdb_id="tt0479997",
    )
    provider = GreekSubsProvider()
    provider.session = Session()

    subtitles = provider.list_subtitles(movie, {Language("ell")})

    assert len(subtitles) == 1
    assert subtitles[0].subtitle_id == "subtitle-id"
    assert subtitles[0].page_link == FRESH_DOWNLOAD_LINK
    assert subtitles[0].version == "Season.of.the.Witch.2011.1080p.bluray.x264.blow"
    assert subtitles[0].uploader == "WhiteAngel"


def test_download_subtitle_refreshes_expired_token(requests_mock):
    requests_mock.get(STALE_DOWNLOAD_LINK, status_code=302)
    requests_mock.get(REFERER, text='<input id="secCode" value="fresh-token">')
    requests_mock.get(
        FRESH_DOWNLOAD_LINK,
        content=b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'attachment; filename="subtitle.srt"',
        },
    )

    subtitle = GreekSubsSubtitle(
        language=Language("ell"),
        page_link=STALE_DOWNLOAD_LINK,
        version="Season-of-the-Witch-2011-1080p-bluray-x264-blow",
        uploader="uploader",
        referer=REFERER,
        subtitle_id="subtitle-id",
    )
    provider = GreekSubsProvider()
    provider.session = Session()

    provider.download_subtitle(subtitle)

    assert subtitle.page_link == FRESH_DOWNLOAD_LINK
    assert subtitle.download_link == FRESH_DOWNLOAD_LINK
    assert subtitle.is_valid()
    assert b"\r\n" not in subtitle.content


def test_download_subtitle_submits_legacy_download_form(requests_mock):
    requests_mock.get(
        FRESH_DOWNLOAD_LINK,
        text=(
            '<input name="langcode" value="el">'
            '<input name="uid" value="user-id">'
            '<input name="output" value="subtitle.srt">'
            '<input name="dll" value="download-id">'
        ),
    )
    requests_mock.post(
        FRESH_DOWNLOAD_LINK,
        content=b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n",
    )
    subtitle = GreekSubsSubtitle(
        language=Language("ell"),
        page_link=FRESH_DOWNLOAD_LINK,
        version="Season-of-the-Witch-2011-1080p-bluray-x264-blow",
        uploader="uploader",
        referer=REFERER,
        subtitle_id="subtitle-id",
    )
    provider = GreekSubsProvider()
    provider.session = Session()

    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()
    assert b"\r\n" not in subtitle.content
