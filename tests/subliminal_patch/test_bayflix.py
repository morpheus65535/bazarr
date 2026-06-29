import io
import zipfile

from subzero.language import Language

from subliminal_patch.providers.bayflix import BayflixProvider
from subliminal_patch.providers.bayflix import BayflixSubtitle


class Response:
    def __init__(self, json_data=None, content=b"", headers=None, status_code=200):
        self._json_data = json_data
        self.content = content
        self.headers = headers or {}
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class Session:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response

    def close(self):
        pass


def make_zip(name="Dune.2021.1080p.WEBRip.x264-SHITBOX.srt"):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(name, b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n")
    return payload.getvalue()


def test_list_subtitles_movie_filters_by_year_and_builds_download_link(movies):
    provider = BayflixProvider()
    provider.session = Session(
        Response(
            [
                {
                    "_id": "dune-2021",
                    "title": "Dune",
                    "description": "Dune.2021.1080p.WEBRip.x264-SHITBOX\n\nFPS: 23.976 | CDs: 1",
                    "release_name": ["Dune.2021.1080p.WEBRip.x264-SHITBOX"],
                    "release_date": "2021-09-15",
                    "media_type": "movie",
                },
                {
                    "_id": "dune-1964",
                    "title": "Woman in the Dunes",
                    "description": "Suna No Onna\n\nFPS: 23.976 | CDs: 2",
                    "release_name": ["Suna.No.Onna.1964"],
                    "release_date": "1964-02-15",
                    "media_type": "movie",
                },
            ]
        )
    )

    subtitles = provider.list_subtitles(movies["dune"], {Language("bul")})

    assert len(subtitles) == 1
    assert subtitles[0].page_link == "https://bayflix.sb/api/subtitles/download/dune-2021"
    assert subtitles[0].fps == 23.976
    assert subtitles[0].num_cds == 1
    assert provider.session.calls[0][1]["params"] == {"title": "Dune"}
    assert subtitles[0].get_matches(movies["dune"]).issuperset({"year", "release_group"})


def test_list_subtitles_episode_filters_to_requested_episode(episodes):
    provider = BayflixProvider()
    provider.session = Session(
        Response(
            [
                {
                    "_id": "bb-s01e01",
                    "title": "Breaking Bad",
                    "description": "Breaking.Bad.S01E01.720p.BluRay.X264-REWARD\n\nFPS: 23.976 | CDs: 1",
                    "release_name": ["Breaking.Bad.S01E01.720p.BluRay.X264-REWARD"],
                    "media_type": "tv",
                },
                {
                    "_id": "bb-s01e02",
                    "title": "Breaking Bad",
                    "description": "Breaking.Bad.S01E02.720p.BluRay.X264-REWARD\n\nFPS: 23.976 | CDs: 1",
                    "release_name": ["Breaking.Bad.S01E02.720p.BluRay.X264-REWARD"],
                    "media_type": "tv",
                },
            ]
        )
    )

    subtitles = provider.list_subtitles(episodes["breaking_bad_s01e01"], {Language("bul")})

    assert len(subtitles) == 1
    assert subtitles[0].id == "bb-s01e01"
    assert provider.session.calls[0][1]["params"] == {"title": "Breaking Bad"}
    assert subtitles[0].get_matches(episodes["breaking_bad_s01e01"]).issuperset(
        {"series", "season", "episode", "release_group"}
    )


def test_download_subtitle_extracts_archive_content(movies):
    provider = BayflixProvider()
    provider.session = Session(Response(content=make_zip()))
    subtitle = BayflixSubtitle(
        language=Language("bul"),
        page_link="https://bayflix.sb/api/subtitles/download/dune-2021",
        file_id="dune-2021",
        title="Dune",
        release_names=["Dune.2021.1080p.WEBRip.x264-SHITBOX"],
        year=2021,
        media_type="movie",
        video=movies["dune"],
    )

    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()
    assert b"\r\n" not in subtitle.content
