# -*- coding: utf-8 -*-
import os

import fese
import pytest
import fese
from fese import FFprobeSubtitleStream
from subliminal_patch.core import Episode, Movie
from subliminal_patch.providers.embeddedsubtitles import EmbeddedSubtitlesProvider
from subzero.language import Language

_DATA = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data")


fese.Language = Language


@pytest.fixture
def video_single_language():
    # Has only ASS streams in english
    return Episode(
        os.path.join(_DATA, "file_1.mkv"),
        "Serial Experiments Lain",
        1,
        1,
        source="Web",
    )


@pytest.fixture
def video_multiple_languages():
    # Has SubRip streams in multiple languages
    return Movie(
        os.path.join(_DATA, "file_2.mkv"),
        "I'm No Longer Here",
        year=2019,
        source="Web",
    )


@pytest.fixture
def config(tmpdir):
    return {
        "include_ass": True,
        "include_srt": True,
        "cache_dir": tmpdir,
        "ffprobe_path": None,
        "ffmpeg_path": None,
        "hi_fallback": False,
    }


@pytest.fixture
def video_inexistent(tmpdir):
    return Movie(
        os.path.join(tmpdir, "inexistent_video.mkv"),
        "Dummy",
        year=2021,
        source="Web",
    )


def test_init(config):
    with EmbeddedSubtitlesProvider(**config) as provider:
        assert provider is not None


def test_inexistent_video(video_inexistent):
    with EmbeddedSubtitlesProvider() as provider:
        subtitles = provider.list_subtitles(video_inexistent, {})
        assert len(subtitles) == 0


@pytest.fixture
def fake_streams():
    return {
        "en_hi": FFprobeSubtitleStream(
            {
                "index": 3,
                "codec_name": "subrip",
                "disposition": {"default": 1, "hearing_impaired": 1},
                "tags": {"language": "eng", "title": "English"},
            }
        ),
        "en": FFprobeSubtitleStream(
            {
                "index": 3,
                "codec_name": "subrip",
                "tags": {"language": "eng", "title": "English"},
            }
        ),
    }


def test_list_subtitles_hi_fallback_one_stream(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            "fese.FFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["en_hi"]],
        )
        fake = fese.FFprobeVideoContainer.get_subtitles("")[0]
        assert fake.disposition.hearing_impaired == True

        subs = provider.list_subtitles(video_single_language, {language})
        assert subs
        assert subs[0].hearing_impaired == False


def test_list_subtitles_hi_fallback_multiple_streams(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            "fese.FFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["en_hi"], fake_streams["en"]],
        )
        subs = provider.list_subtitles(video_single_language, {language})
        assert len(subs) == 2
        assert subs[0].hearing_impaired == True
        assert subs[1].hearing_impaired == False


def test_list_subtitles_hi_fallback_multiple_hi_streams(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            "fese.FFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["en_hi"], fake_streams["en_hi"]],
        )
        subs = provider.list_subtitles(video_single_language, {language})
        assert len(subs) == 2
        assert subs[0].hearing_impaired == False
        assert subs[1].hearing_impaired == False


def test_list_subtitles_only_forced(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        language = Language.fromalpha2("en")
        language = Language.rebuild(language, forced=True)
        subs = provider.list_subtitles(video_single_language, {language})
        assert len(subs) == 0


def test_list_subtitles_also_forced(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        language_1 = Language.fromalpha2("en")
        language_2 = Language.rebuild(language_1, forced=True)
        subs = provider.list_subtitles(video_single_language, {language_1, language_2})
        assert any(language_1 == sub.language for sub in subs)
        assert any(not sub.language.forced for sub in subs)


def test_list_subtitles_single_language(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        subs = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )

        for sub in subs:
            assert sub.language == Language.fromalpha2("en")


def test_list_subtitles_multiple_languages(video_multiple_languages):
    with EmbeddedSubtitlesProvider() as provider:
        languages = {Language.fromalpha2(code) for code in ("en", "it", "fr", "es")} | {
            Language("por", "BR")
        }

        subs = provider.list_subtitles(video_multiple_languages, languages)
        for expected in languages:
            assert any(sub.language == expected for sub in subs)


def test_list_subtitles_wo_ass(video_single_language):
    with EmbeddedSubtitlesProvider(include_ass=False) as provider:
        subs = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )
        assert not subs


def test_list_subtitles_wo_srt(video_multiple_languages):
    with EmbeddedSubtitlesProvider(include_srt=False) as provider:
        subs = provider.list_subtitles(
            video_multiple_languages, {Language.fromalpha2("en")}
        )
        assert not subs


def test_download_subtitle_multiple(video_multiple_languages):
    with EmbeddedSubtitlesProvider() as provider:
        languages = {Language.fromalpha2(code) for code in ("en", "it", "fr")} | {
            Language("por", "BR")
        }

        subs = provider.list_subtitles(video_multiple_languages, languages)
        for sub in subs:
            provider.download_subtitle(sub)
            assert sub.content is not None


def test_download_subtitle_single(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        subtitle = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )[0]
        provider.download_subtitle(subtitle)
        assert subtitle.content is not None


def test_download_invalid_subtitle(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        subtitle = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )[0]

        provider._cached_paths[subtitle.container.path] = {
            subtitle.stream.index: "dummy.srt"
        }
        with pytest.raises(fese.InvalidFile):
            provider.download_subtitle(subtitle)
