# -*- coding: utf-8 -*-
import os

from fese import FFprobeSubtitleStream
from fese import FFprobeVideoContainer
from fese import tags
from fese.exceptions import LanguageNotFound
import pytest
from subliminal_patch.core import Episode
from subliminal_patch.core import Movie
from subliminal_patch.providers.embeddedsubtitles import _clean_ass_subtitles
from subliminal_patch.providers.embeddedsubtitles import (
    _discard_possible_incomplete_subtitles,
)
from subliminal_patch.providers.embeddedsubtitles import _get_pretty_release_name
from subliminal_patch.providers.embeddedsubtitles import _MemoizedFFprobeVideoContainer
from subliminal_patch.providers.embeddedsubtitles import EmbeddedSubtitlesProvider
from subzero.language import Language

tags.Language = Language


@pytest.fixture
def video_single_language(data):
    # Has only ASS streams in english
    return Episode(
        os.path.join(data, "file_1.mkv"),
        "Serial Experiments Lain",
        1,
        1,
        source="Web",
    )


@pytest.fixture
def video_multiple_languages(data):
    # Has SubRip streams in multiple languages
    return Movie(
        os.path.join(data, "file_2.mkv"),
        "I'm No Longer Here",
        year=2019,
        source="Web",
    )


@pytest.fixture
def config(tmpdir):
    return {
        "included_codecs": None,
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


def test_language_is_subzero_type():
    assert tags.Language == Language


def test_init(config):
    with EmbeddedSubtitlesProvider(**config) as provider:
        assert provider is not None


def test_init_empty_included_codecs():
    with EmbeddedSubtitlesProvider(included_codecs=[]) as provider:
        assert provider._included_codecs == {"ass", "subrip", "webvtt", "mov_text"}


def test_init_custom_included_codecs():
    with EmbeddedSubtitlesProvider(included_codecs=["ass"]) as provider:
        assert provider._included_codecs == {"ass"}


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
        "tg": FFprobeSubtitleStream(
            {
                "index": 3,
                "codec_name": "subrip",
                "tags": {"language": "fil", "title": "Filipino"},
            }
        ),
        "es_hi": FFprobeSubtitleStream(
            {
                "index": 3,
                "codec_name": "subrip",
                "disposition": {"default": 1, "hearing_impaired": 1},
                "tags": {"language": "spa", "title": "Spanish"},
            }
        ),
        "es": FFprobeSubtitleStream(
            {
                "index": 3,
                "codec_name": "subrip",
                "tags": {"language": "spa", "title": "Spanish"},
            }
        ),
    }


@pytest.mark.parametrize("tags_", [{}, {"language": "und", "title": "Unknown"}])
def test_list_subtitles_unknown_as_fallback(mocker, tags_, video_single_language):
    with EmbeddedSubtitlesProvider(
        unknown_as_fallback=True, fallback_lang="en"
    ) as provider:
        fake = FFprobeSubtitleStream(
            {"index": 3, "codec_name": "subrip", "tags": tags_}
        )
        mocker.patch(
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[fake],
        )
        result = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )
        assert len(result) == 1


def test_list_subtitles_unknown_as_fallback_w_real_english_subtitles(
    video_single_language, mocker
):
    with EmbeddedSubtitlesProvider(
        unknown_as_fallback=True, fallback_lang="en"
    ) as provider:
        fakes = [
            FFprobeSubtitleStream(
                {"index": 3, "codec_name": "subrip", "tags": {"language": "und"}}
            ),
            FFprobeSubtitleStream(
                {"index": 2, "codec_name": "subrip", "tags": {"language": "eng"}}
            ),
        ]
        mocker.patch(
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=fakes,
        )
        result = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )
        assert len(result) == 1


@pytest.mark.parametrize("tags_", [{}, {"language": "und", "title": "Unknown"}])
def test_list_subtitles_unknown_as_fallback_disabled(tags_):
    with EmbeddedSubtitlesProvider(unknown_as_fallback=False, fallback_lang="en"):
        with pytest.raises(LanguageNotFound):
            assert FFprobeSubtitleStream(
                {"index": 3, "codec_name": "subrip", "tags": tags_}
            )


def test_list_subtitles_hi_fallback_one_stream(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["en_hi"]],
        )
        fake = _MemoizedFFprobeVideoContainer.get_subtitles("")[0]
        assert fake.disposition.hearing_impaired == True
        subs = provider.list_subtitles(video_single_language, {language})
        assert subs[0].language == Language("eng", hi=False)
        assert subs[0].hearing_impaired == False


def test_list_subtitles_custom_language_from_fese(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language("tgl", "PH")
        mocker.patch(
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["tg"]],
        )
        assert provider.list_subtitles(video_single_language, {language})


def test_list_subtitles_hi_fallback_multiple_streams(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            # "fese.FFprobeVideoContainer.get_subtitles",
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[fake_streams["en_hi"], fake_streams["en"]],
        )
        subs = provider.list_subtitles(video_single_language, {language})
        assert len(subs) == 1
        assert subs[0].language == Language("eng", hi=False)


def test_list_subtitles_hi_fallback_multiple_language_streams(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        languages = {Language.fromalpha2("en"), Language.fromalpha2("es")}
        mocker.patch(
            # "fese.FFprobeVideoContainer.get_subtitles",
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[
                fake_streams["en_hi"],
                fake_streams["es"],
                fake_streams["es_hi"],
            ],
        )
        subs = provider.list_subtitles(video_single_language, languages)
        assert len(subs) == 2
        assert subs[0].hearing_impaired == False  # English subittle
        assert subs[1].hearing_impaired == False  # Spanish subtitle


def test_list_subtitles_hi_fallback_multiple_language_streams_multiple_input_languages(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        languages = {
            Language.fromalpha2("en"),
            Language.fromalpha2("es"),
            Language("spa", hi=True),
        }
        mocker.patch(
            # "fese.FFprobeVideoContainer.get_subtitles",
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
            return_value=[
                fake_streams["en_hi"],
                fake_streams["es"],
                fake_streams["es_hi"],
            ],
        )
        subs = provider.list_subtitles(video_single_language, languages)
        assert len(subs) == 3


def test_list_subtitles_hi_fallback_multiple_hi_streams(
    video_single_language, fake_streams, mocker
):
    with EmbeddedSubtitlesProvider(hi_fallback=True) as provider:
        language = Language.fromalpha2("en")
        mocker.patch(
            # "fese.FFprobeVideoContainer.get_subtitles",
            "subliminal_patch.providers.embeddedsubtitles._MemoizedFFprobeVideoContainer.get_subtitles",
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
    with EmbeddedSubtitlesProvider(included_codecs=("srt",)) as provider:
        subs = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )
        assert not subs


def test_list_subtitles_wo_srt(video_multiple_languages):
    with EmbeddedSubtitlesProvider(included_codecs=("ass",)) as provider:
        subs = provider.list_subtitles(
            video_multiple_languages, {Language.fromalpha2("en")}
        )
        assert not subs


def test_get_pretty_release_name():
    stream = FFprobeSubtitleStream(
        {
            "index": 1,
            "codec_name": "subrip",
            "tags": {"language": "eng", "title": "forced"},
        }
    )
    container = FFprobeVideoContainer("foo.mkv")
    assert _get_pretty_release_name(stream, container) == "foo.en.forced.srt"


def test_clean_ass_subtitles(data, tmp_path):
    path = os.path.join(data, "subs.ass")

    with open(path, "r") as f:
        og_lines_len = len(f.readlines())

    output_path = os.path.join(tmp_path, "subs.ass")

    _clean_ass_subtitles(path, output_path)

    with open(output_path, "r") as f:
        assert og_lines_len > len(f.readlines())


def test_download_subtitle_multiple(video_multiple_languages):
    with EmbeddedSubtitlesProvider() as provider:
        languages = {Language.fromalpha2(code) for code in ("en", "it", "fr")} | {
            Language("por", "BR")
        }

        subs = provider.list_subtitles(video_multiple_languages, languages)
        for sub in subs:
            provider.download_subtitle(sub)
            assert sub.is_valid()


def test_download_subtitle_single(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        subtitle = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )[0]
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()


def test_download_subtitle_single_is_ass(video_single_language):
    with EmbeddedSubtitlesProvider() as provider:
        subtitle = provider.list_subtitles(
            video_single_language, {Language.fromalpha2("en")}
        )[0]
        provider.download_subtitle(subtitle)
        assert subtitle.is_valid()

        assert subtitle.format == "srt"

        subtitle.use_original_format = True

        assert subtitle.format == "ass"


def test_memoized(video_single_language, mocker):
    with EmbeddedSubtitlesProvider() as provider:
        provider.list_subtitles(video_single_language, {Language.fromalpha2("en")})

    with EmbeddedSubtitlesProvider() as provider:
        mocker.patch("fese.FFprobeVideoContainer.get_subtitles")
        assert (
            provider.list_subtitles(video_single_language, {Language.fromalpha2("en")})[
                0
            ]
            is not None
        )


@pytest.mark.parametrize(
    "number_of_frames,expected_len",
    [((34, 811), 1), ((0, 0), 2), ((811, 34), 1), ((900, 1000), 2), ((0, 900), 1)],
)
def test_discard_possible_incomplete_subtitles(number_of_frames, expected_len):
    subtitle_1 = FFprobeSubtitleStream(
        {
            "index": 1,
            "codec_name": "subrip",
            "codec_long_name": "SubRip subtitle",
            "disposition": {},
            "tags": {"language": "eng", "NUMBER_OF_FRAMES": number_of_frames[0]},
        }
    )
    subtitle_2 = FFprobeSubtitleStream(
        {
            "index": 2,
            "codec_name": "subrip",
            "codec_long_name": "SubRip subtitle",
            "disposition": {},
            "tags": {"language": "eng", "NUMBER_OF_FRAMES": number_of_frames[1]},
        }
    )
    new_list = _discard_possible_incomplete_subtitles([subtitle_1, subtitle_2])
    assert len(new_list) == expected_len
