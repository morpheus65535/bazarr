"""Development compatibility properties and case-insensitive extensions."""

from itertools import product

import pytest

from utilities.media_codecs import (radarr_audio_codec, radarr_video_codec, sonarr_audio_codec,
                                   sonarr_codecs, sonarr_video_codec)


def test_nullable_sonarr_audio_aliases_and_unknown_values() -> None:
    aliases = {
        'ac-3': 'AC3',
        'e-ac-3': 'EAC3',
        'mpeg audio': 'MP3',
    }
    unknown_values = _unknown_unicode_values()
    values = (None, 'AC-3', 'E-AC-3', 'MPEG Audio', *unknown_values)

    for value in values:
        expected = None if value is None else aliases.get(value.casefold(), value)
        assert sonarr_audio_codec(value) == expected


def test_nullable_sonarr_video_alias_prefix_suffix_and_unknown_properties() -> None:
    exact_aliases = {
        'x264': 'h264', 'avc': 'h264', 'x265': 'h265', 'hevc': 'h265',
        'mpeg-1 video': 'Mpeg', 'mpeg-2 video': 'Mpeg2',
        'mpeg-4 video': 'Mpeg4', 'vc-1': 'VC1',
    }
    prefixes = {'xvid': 'XviD', 'divx': 'DivX'}
    suffixes = {'vp6': 'VP6', 'vp7': 'VP7', 'vp8': 'VP8', 'vp9': 'VP9'}
    unknown_values = _unknown_unicode_values()
    values = (None, 'x264', 'AVC', 'x265', 'HEVC', 'MPEG-1 Video', 'MPEG-2 Video',
              'MPEG-4 Video', 'VC-1', 'XviD build', 'DivX build',
              'On2 VP6', 'On2 VP7', 'On2 VP8', 'On2 VP9', *unknown_values)

    for value in values:
        if value is None:
            expected = None
        else:
            folded = value.casefold()
            expected = next((result for prefix, result in prefixes.items() if folded.startswith(prefix)), None)
            if expected is None:
                expected = suffixes.get(folded[-3:], exact_aliases.get(folded, value))
        assert sonarr_video_codec(value) == expected


def test_radarr_audio_optional_metadata_and_format_relevance() -> None:
    # Metadata is relevant only to its matching format. Each finite product
    # includes absent, empty, matching, contradictory, and unknown metadata.
    metadata_values = (None, '', 'A_AAC/MPEG4/LC/SBR', '55', 'A_MPEG/L3', 'A_MPEG/L2',
                       'Layer 3', 'Layer 2', '16-ch', 'other')
    for identifier, profile, features in product(metadata_values, repeat=3):
        assert radarr_audio_codec('AAC', identifier, profile, features) == (
            'HE-AAC' if identifier == 'A_AAC/MPEG4/LC/SBR' else 'AAC'
        )
        assert radarr_audio_codec('MLP FBA', identifier, profile, features) == (
            'TrueHD Atmos' if features == '16-ch' else 'TrueHD'
        )
        mpeg_expected = (
            'MP3' if identifier in ('55', 'A_MPEG/L3') or profile == 'Layer 3'
            else 'MP2' if identifier == 'A_MPEG/L2' or profile == 'Layer 2'
            else None
        )
        assert radarr_audio_codec('MPEG Audio', identifier, profile, features) == mpeg_expected


def test_radarr_audio_mpeg_layer3_has_precedence_over_layer2() -> None:
    identifiers = (None, '', '55', 'A_MPEG/L3', 'A_MPEG/L2', 'unknown')
    profiles = (None, '', 'Layer 3', 'Layer 2', 'unknown')
    for identifier, profile in product(identifiers, profiles):
        expected = ('MP3' if identifier in ('55', 'A_MPEG/L3') or profile == 'Layer 3'
                    else 'MP2' if identifier == 'A_MPEG/L2' or profile == 'Layer 2' else None)
        assert radarr_audio_codec('MPEG Audio', identifier, profile, None) == expected


def test_radarr_audio_aliases_and_unknown_unicode_round_trip() -> None:
    aliases = {'ac-3': 'AC3', 'e-ac-3': 'EAC3'}
    unknown_values = _unknown_unicode_values()
    values = (None, 'AC-3', 'E-AC-3', *unknown_values)
    metadata = (None, '', 'irrelevant', '55', 'A_MPEG/L3', 'Layer 2', '16-ch')
    for value, identifier, profile, features in product(values, metadata, metadata, metadata):
        expected = None if value is None else aliases.get(value.casefold(), value)
        assert radarr_audio_codec(value, identifier, profile, features) == expected


def test_radarr_video_format_metadata_is_scoped_to_matching_formats() -> None:
    metadata_values = (None, '', '2', 'V_MPEG2', '1', 'XVID', 'DIVX', 'DX50', 'XviD 1.3',
                       'DivX 6', 'x265 3.5', 'other')
    aliases = ((None, None), ('', ''), ('x264', 'h264'), ('AVC', 'h264'),
               ('V.MPEG4/ISO/AVC', 'h264'), ('MPEG-1 Video', 'Mpeg'), ('MPEG-2 Video', 'Mpeg2'),
               ('VC-1', 'VC1'), ('WMV2', 'WMV'), ('DivX', 'DivX'), ('div3', 'DivX'),
               (' vendor ', ' vendor '), ('音声', '音声'))
    for (value, expected), identifier, library in product(aliases, metadata_values, metadata_values):
        assert radarr_video_codec(value, identifier, library) == expected


def test_radarr_video_mpeg_visual_encoder_precedence_and_prefix_suffix() -> None:
    # Every known identifier ending is paired with every known library prefix
    # to cover precedence when the metadata disagrees.
    identifiers = (None, '', 'XVID', 'otherXVID', 'DIV3', 'DIVX', 'DX50', 'other')
    libraries = (None, '', 'XviD 1.3', 'XviD encoder', 'DivX 6', 'DivX encoder', 'other')
    for identifier, library in product(identifiers, libraries):
        result = radarr_video_codec('MPEG-4 Visual', identifier, library)
        if not identifier or not library:
            expected = 'MPEG-4 Visual'
        elif identifier.casefold().endswith('xvid') or library.casefold().startswith('xvid'):
            expected = 'XviD'
        elif identifier.casefold().endswith(('div3', 'divx', 'dx50')) or library.casefold().startswith('divx'):
            expected = 'DivX'
        else:
            expected = None
        assert result == expected


@pytest.mark.parametrize(('codec_id', 'expected'), [('2', 'Mpeg2'), ('V_MPEG2', 'Mpeg2'),
                                                    ('1', 'Mpeg'), ('unknown', 'Mpeg')])
def test_radarr_mpeg_video_requires_identifier(codec_id: str, expected: str) -> None:
    assert radarr_video_codec('MPEG Video', codec_id, None) == expected
    assert radarr_video_codec('MPEG Video', None, None) == 'MPEG Video'
    assert radarr_video_codec('MPEG Video', '', 'unused') == 'MPEG Video'


def test_radarr_hevc_unresolved_result_differs_from_missing_library() -> None:
    for value, identifier, library in product(('HEVC', 'V_MPEGH/ISO/HEVC'),
                                               (None, '', 'other', '2', 'XVID'),
                                               (None, '', 'x265', 'x265 build', 'x264 build', 'other')):
        expected = value if not library else 'h265' if library.startswith('x265') else None
        assert radarr_video_codec(value, identifier, library) == expected


def test_generated_sonarr_video_prefixes_take_precedence_over_suffixes() -> None:
    for value, (prefix, codec), suffix in product(_unknown_unicode_values(),
                                                 (('XviD', 'XviD'), ('DivX', 'DivX')),
                                                 ('VP6', 'VP7', 'VP8', 'VP9')):
        assert sonarr_video_codec(prefix + value + suffix) == codec
    for value, suffix in product(_unknown_unicode_values(), ('VP6', 'VP7', 'VP8', 'VP9')):
        assert sonarr_video_codec(value + suffix) == suffix


def test_radarr_mp3_whitespace_does_not_depend_on_metadata() -> None:
    for before, after, identifier in product(('', ' ', '\t', '\n', '\u2003'), repeat=3):
        assert radarr_audio_codec(before + 'mp3' + after, identifier, 'Layer 2', '16-ch') == 'MP3'


def test_generated_unknown_unicode_codec_names_are_preserved() -> None:
    for value in _unknown_unicode_values():
        assert sonarr_audio_codec(value) == value
        assert sonarr_video_codec(value) == value
        assert radarr_audio_codec(value, None, None, None) == value
        assert radarr_video_codec(value, None, None) == value


def _unknown_unicode_values() -> tuple[str, ...]:
    # Deterministically generate 1–3 character strings across ASCII, combining
    # marks, astral symbols, and multiple scripts. The chosen alphabet cannot
    # form any recognized alias, video prefix, or VP suffix.
    alphabet = ('q', 'Z', '_', '🚀', 'é', '\u0301', 'К', '音', '\u0000', '\n')
    return tuple(''.join(parts) for length in (0, 1, 2, 3)
                 for parts in product(alphabet, repeat=length))


def test_case_insensitive_alias_extensions() -> None:
    # These variants intentionally extend the historical development
    # converters, which recognized the canonical spellings above only.
    sonarr_audio = {'AC-3': 'AC3', 'E-AC-3': 'EAC3', 'MPEG AUDIO': 'MP3'}
    sonarr_video = {'X264': 'h264', 'aVc': 'h264', 'HeVc': 'h265', 'vC-1': 'VC1'}
    radarr_audio = {'AC-3': 'AC3', 'E-AC-3': 'EAC3', 'aAc': 'AAC', 'MPEG AUDIO': None}
    radarr_video = {'aVc': 'h264', 'WmV2': 'WMV', 'DIVX': 'DivX'}
    for value, expected in sonarr_audio.items():
        assert sonarr_audio_codec(value) == expected
    for value, expected in sonarr_video.items():
        assert sonarr_video_codec(value) == expected
    for value, expected in radarr_audio.items():
        assert radarr_audio_codec(value, None, None, None) == expected
    for value, expected in radarr_video.items():
        assert radarr_video_codec(value, None, None) == expected


def test_case_insensitive_codec_metadata_extensions() -> None:
    assert radarr_audio_codec('aac', 'a_aac/mpeg4/lc/sbr', None, None) == 'HE-AAC'
    assert radarr_audio_codec('mpeg audio', 'a_mpeg/l2', 'lAyEr 3', None) == 'MP3'
    assert radarr_audio_codec('mlp fba', None, None, '16-CH') == 'TrueHD Atmos'
    assert radarr_video_codec('hevc', None, 'X265 build') == 'h265'
    assert radarr_video_codec('mpeg video', 'v_mpeg2', None) == 'Mpeg2'
    assert radarr_video_codec('mpeg-4 visual', 'xvid', 'dIvX') == 'XviD'


def test_casefold_unicode_matches_and_near_misses() -> None:
    assert radarr_audio_codec('AAC', 'A_AAC/MPEG4/LC/ſBR', None, None) == 'HE-AAC'
    assert radarr_video_codec('MPEG-4 Viſual', 'XVID', 'DivX') == 'XviD'
    assert radarr_video_codec('V_MPEGH/IſO/HEVC', None, 'x265') == 'h265'
    for value in ('MPEG-4 VİDEO', 'DıvX', 'XVİD', 'MPEG-4 Vısual'):
        assert sonarr_audio_codec(value) == value
        assert sonarr_video_codec(value) == value
        assert radarr_audio_codec(value, None, None, None) == value
        assert radarr_video_codec(value, 'XVID', 'DivX') == value


def test_codec_caches_remain_bounded_and_work_after_eviction() -> None:
    codecs = (sonarr_codecs, radarr_audio_codec, radarr_video_codec)
    for codec in codecs:
        codec.cache_clear()
    try:
        for index in range(1024):
            value = f'vendor codec {index}'
            assert sonarr_audio_codec(value) == value
            assert sonarr_video_codec(value) == value
            assert sonarr_codecs(value, value) == (value, value)
            assert radarr_audio_codec(value, None, None, None) == value
            assert radarr_video_codec(value, None, None) == value
        for codec in codecs:
            assert codec.cache_info().currsize == codec.cache_info().maxsize == 128
        for _ in range(2):
            assert sonarr_audio_codec('ac-3') == 'AC3'
            assert sonarr_video_codec('xViD encoder VP9') == 'XviD'
            assert sonarr_codecs('ac-3', 'xViD encoder VP9') == ('AC3', 'XviD')
            assert radarr_audio_codec('aac', 'a_aac/mpeg4/lc/sbr', None, None) == 'HE-AAC'
            assert radarr_video_codec('hevc', None, 'X265 encoder') == 'h265'
        for codec in codecs:
            assert codec.cache_info().hits == 1
    finally:
        for codec in codecs:
            codec.cache_clear()


def test_sonarr_cached_pairs_preserve_each_codec_independently() -> None:
    audio_values = (None, '', 'none', 'AAC', 'AC-3', 'e-aC-3', 'mPeG aUdIo', 'Opus', '音声', ' AAC ')
    video_values = (None, '', 'none', 'x264', 'aVc', 'HeVc', 'MPEG-4 Video',
                    'xViD encoder VP9', 'dIvX encoder VP8', 'On2 vP9', 'AV1', '音声', ' AVC ')
    for audio, video in product(audio_values, video_values):
        expected = sonarr_audio_codec(audio), sonarr_video_codec(video)
        assert sonarr_codecs(audio, video) == expected
        assert sonarr_codecs(audio, video) == expected
