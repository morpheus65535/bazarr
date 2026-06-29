import io
import zipfile

from subzero.language import Language

from subliminal_patch.providers.vladoonmooo import VladoonMoooProvider
from subliminal_patch.providers.vladoonmooo import VladoonMoooSubtitle


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


def make_zip(name="breaking.bad.s01e01.720p.bluray.x264-reward.srt"):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr(name, b"1\r\n00:00:01,000 --> 00:00:02,000\r\nHello\r\n")
    return payload.getvalue()


def test_list_subtitles_episode_accepts_matching_season_pack(episodes):
    provider = VladoonMoooProvider()
    provider.session = Session(
        Response(
            {
                "results": [
                    {
                        "id": 20554,
                        "original_title": "Breaking Bad",
                        "title": "Breaking Bad",
                        "type": "tv",
                        "season": 1,
                        "episode": None,
                        "episode_type": "season",
                        "imdb_id": "tt0903747",
                        "release_names": [
                            "breaking.bad.s01e01.720p.bluray.x264-reward",
                            "breaking.bad.s01e02.720p.bluray.x264-reward",
                        ],
                        "uploaded_by": "Vlad00n",
                    }
                ]
            }
        )
    )

    subtitles = provider.list_subtitles(episodes["breaking_bad_s01e01"], {Language("bul")})

    assert len(subtitles) == 1
    assert subtitles[0].page_link == "https://vladoon.mooo.com/subs/download/20554"
    assert provider.session.calls[0][1]["params"] == {"q": "Breaking Bad S01E01"}
    assert subtitles[0].get_matches(episodes["breaking_bad_s01e01"]).issuperset(
        {"series", "season", "episode", "release_group", "imdb_id"}
    )


def test_list_subtitles_movie_prefers_imdb_match(movies):
    provider = VladoonMoooProvider()
    provider.session = Session(
        Response(
            {
                "results": [
                    {
                        "id": 15800,
                        "original_title": "Dune",
                        "title": "Dune",
                        "type": "movie",
                        "imdb_id": "tt1160419",
                        "release_names": ["Dune.2021.1080p.WEBRip.x264-SHITBOX"],
                    },
                    {
                        "id": 15801,
                        "original_title": "Dune: Part Two",
                        "title": "Dune: Part Two",
                        "type": "movie",
                        "imdb_id": "tt15239678",
                        "release_names": ["Dune.Part.Two.2024.720p.WEB.h264-EDITH"],
                    },
                ]
            }
        )
    )

    subtitles = provider.list_subtitles(movies["dune"], {Language("bul")})

    assert len(subtitles) == 1
    assert subtitles[0].id == "15800"
    assert subtitles[0].get_matches(movies["dune"]).issuperset({"imdb_id", "release_group"})


def test_download_subtitle_extracts_archive_content(episodes):
    provider = VladoonMoooProvider()
    provider.session = Session(Response(content=make_zip()))
    subtitle = VladoonMoooSubtitle(
        language=Language("bul"),
        page_link="https://vladoon.mooo.com/subs/download/20554",
        file_id=20554,
        title="Breaking Bad",
        release_names=["breaking.bad.s01e01.720p.bluray.x264-reward"],
        imdb_id="tt0903747",
        media_type="episode",
        video=episodes["breaking_bad_s01e01"],
    )

    provider.download_subtitle(subtitle)

    assert subtitle.is_valid()
    assert b"\r\n" not in subtitle.content
