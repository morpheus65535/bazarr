import pytest

from utilities.media_codecs import radarr_audio_codec, radarr_video_codec, sonarr_audio_codec, sonarr_video_codec


@pytest.mark.parametrize(('codec', 'expected'), [
    (None, None), ('', ''), ('AC-3', 'AC3'), ('E-AC-3', 'EAC3'), ('MPEG Audio', 'MP3'), ('AAC', 'AAC'),
    ('ac-3', 'AC3'), ('e-Ac-3', 'EAC3'), ('mPeG aUdIo', 'MP3'), ('VeNdOr Codec ', 'VeNdOr Codec '),
])
def test_sonarr_audio_codec(codec: str | None, expected: str | None) -> None:
    assert sonarr_audio_codec(codec) == expected


@pytest.mark.parametrize(('codec', 'expected'), [
    (None, None), ('', ''), ('x264', 'h264'), ('AVC', 'h264'), ('x265', 'h265'), ('HEVC', 'h265'),
    ('XviD 1.3', 'XviD'), ('DivX 6', 'DivX'), ('MPEG-1 Video', 'Mpeg'), ('MPEG-2 Video', 'Mpeg2'),
    ('MPEG-4 Video', 'Mpeg4'), ('VC-1', 'VC1'), ('On2 VP6', 'VP6'), ('On2 VP7', 'VP7'),
    ('On2 VP8', 'VP8'), ('On2 VP9', 'VP9'), ('AV1', 'AV1'),
    ('XviD VP8', 'XviD'), ('DivX VP9', 'DivX'), ('vp9', 'VP9'), ('x264 ', 'x264 '),
    ('aVc', 'h264'), ('HeVc', 'h265'), ('mPeG-4 ViDeO', 'Mpeg4'), ('vC-1', 'VC1'),
    ('xViD vp8', 'XviD'), ('dIVx vp9', 'DivX'), ('oN2 vP6', 'VP6'), ('VeNdOr Codec ', 'VeNdOr Codec '),
])
def test_sonarr_video_codec(codec: str | None, expected: str | None) -> None:
    assert sonarr_video_codec(codec) == expected


@pytest.mark.parametrize(('codec', 'identifier', 'profile', 'features', 'expected'), [
    (None, None, None, None, None), ('', None, None, None, ''),
    ('AC-3', None, None, None, 'AC3'), ('E-AC-3', None, None, None, 'EAC3'),
    ('AAC', 'A_AAC/MPEG4/LC/SBR', None, None, 'HE-AAC'), ('AAC', None, None, None, 'AAC'),
    (' mp3 ', None, None, None, 'MP3'), ('MPEG Audio', '55', None, None, 'MP3'),
    ('MPEG Audio', 'A_MPEG/L3', None, None, 'MP3'), ('MPEG Audio', None, 'Layer 3', None, 'MP3'),
    ('MPEG Audio', 'A_MPEG/L2', None, None, 'MP2'), ('MPEG Audio', None, 'Layer 2', None, 'MP2'),
    ('MPEG Audio', 'A_MPEG/L2', 'Layer 3', None, 'MP3'),
    ('MPEG Audio', 'A_MPEG/L3', 'Layer 2', None, 'MP3'),
    ('MPEG Audio', None, None, None, None), ('MLP FBA', None, None, '16-ch', 'TrueHD Atmos'),
    ('MLP FBA', None, None, None, 'TrueHD'), ('FLAC', None, None, None, 'FLAC'),
    ('AAC', '55', 'Layer 3', '16-ch', 'AAC'), ('MP3', None, None, None, 'MP3'),
    (' AC-3 ', None, None, None, ' AC-3 '),
    ('ac-3', None, None, None, 'AC3'), ('e-Ac-3', None, None, None, 'EAC3'),
    ('aAc', 'a_aac/mpeg4/lc/sbr', None, None, 'HE-AAC'), ('aac', None, None, None, 'AAC'),
    ('mPeG aUdIo', 'a_mpeg/l2', 'lAyEr 3', None, 'MP3'),
    ('mpeg audio', 'a_mpeg/l3', 'layer 2', None, 'MP3'),
    ('MPEG AUDIO', None, 'LAYER 2', None, 'MP2'),
    ('mLp FbA', None, None, '16-CH', 'TrueHD Atmos'), ('mlp fba', None, None, None, 'TrueHD'),
    (' Mp3 ', None, None, None, 'MP3'), ('VeNdOr Codec ', '55', 'Layer 3', '16-ch', 'VeNdOr Codec '),
])
def test_radarr_audio_codec(codec: str | None, identifier: str | None, profile: str | None,
                            features: str | None, expected: str | None) -> None:
    assert radarr_audio_codec(codec, identifier, profile, features) == expected


@pytest.mark.parametrize(('codec', 'identifier', 'library', 'expected'), [
    (None, None, None, None), ('', None, None, ''), ('x264', None, None, 'h264'),
    ('AVC', None, None, 'h264'), ('V.MPEG4/ISO/AVC', None, None, 'h264'),
    ('HEVC', None, 'x265 3.5', 'h265'), ('V_MPEGH/ISO/HEVC', None, 'x265', 'h265'),
    ('HEVC', None, None, 'HEVC'), ('HEVC', None, 'other', None),
    ('MPEG Video', '2', None, 'Mpeg2'), ('MPEG Video', 'V_MPEG2', None, 'Mpeg2'),
    ('MPEG Video', '1', None, 'Mpeg'), ('MPEG-1 Video', None, None, 'Mpeg'),
    ('MPEG-2 Video', None, None, 'Mpeg2'), ('MPEG-4 Visual', 'XVID', 'other', 'XviD'),
    ('MPEG-4 Visual', 'other', 'XviD 1.3', 'XviD'), ('MPEG-4 Visual', 'DIV3', 'other', 'DivX'),
    ('MPEG-4 Visual', 'DIVX', 'other', 'DivX'), ('MPEG-4 Visual', 'DX50', 'other', 'DivX'),
    ('MPEG-4 Visual', 'other', 'DivX 6', 'DivX'), ('MPEG-4 Visual', 'other', 'other', None),
    ('VC-1', None, None, 'VC1'), ('WMV2', None, None, 'WMV'), ('div3', None, None, 'DivX'),
    ('DivX', None, None, 'DivX'), ('AV1', None, None, 'AV1'),
    ('HEVC', None, '', 'HEVC'), ('V_MPEGH/ISO/HEVC', None, 'other', None),
    ('MPEG Video', None, None, 'MPEG Video'), ('MPEG Video', '', None, 'MPEG Video'),
    ('MPEG-4 Visual', None, 'XviD', 'MPEG-4 Visual'),
    ('MPEG-4 Visual', 'XVID', None, 'MPEG-4 Visual'),
    ('MPEG-4 Visual', 'DIVX', '', 'MPEG-4 Visual'),
    ('MPEG-4 Visual', 'XVID', 'DivX', 'XviD'), ('MPEG-4 Visual', 'DIVX', 'XviD', 'XviD'),
    ('x265', None, None, 'x265'),
    ('aVc', None, None, 'h264'), ('v.MpEg4/IsO/aVc', None, None, 'h264'),
    ('hEvC', None, 'X265 3.5', 'h265'), ('v_MpEgH/iSo/HeVc', None, 'X265', 'h265'),
    ('hevc', None, None, 'hevc'), ('hevc', None, 'Other', None),
    ('mPeG vIdEo', 'v_mpeg2', None, 'Mpeg2'), ('MPEG VIDEO', '1', None, 'Mpeg'),
    ('mpeg-4 visual', 'xvid', 'dIvX', 'XviD'), ('MPEG-4 VISUAL', 'divx', 'xVId', 'XviD'),
    ('mpeg-4 visual', 'dx50', 'Other', 'DivX'), ('mpeg-4 visual', 'Other', 'dIvX 6', 'DivX'),
    ('DIVX', None, None, 'DivX'), ('WmV2', None, None, 'WMV'),
    ('VeNdOr Codec ', 'XVID', 'XviD', 'VeNdOr Codec '),
])
def test_radarr_video_codec(codec: str | None, identifier: str | None, library: str | None,
                            expected: str | None) -> None:
    assert radarr_video_codec(codec, identifier, library) == expected
