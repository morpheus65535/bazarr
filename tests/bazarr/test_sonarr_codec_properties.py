"""Deterministic properties for Sonarr codec normalization."""

from itertools import product

from utilities.media_codecs import sonarr_audio_codec, sonarr_video_codec


def test_sonarr_audio_canonical_aliases_and_nullable_identity() -> None:
    aliases = {'AC-3': 'AC3', 'E-AC-3': 'EAC3', 'MPEG Audio': 'MP3'}
    values = (None, '', *aliases, 'AAC', 'vendor codec ', '  AC-3  ')
    for value in values:
        expected = None if value is None else aliases.get(value, value)
        assert sonarr_audio_codec(value) == expected


def test_sonarr_video_canonical_aliases_and_nullable_identity() -> None:
    aliases = {
        'x264': 'h264', 'AVC': 'h264', 'x265': 'h265', 'HEVC': 'h265',
        'MPEG-1 Video': 'Mpeg', 'MPEG-2 Video': 'Mpeg2',
        'MPEG-4 Video': 'Mpeg4', 'VC-1': 'VC1',
    }
    values = (None, '', *aliases, 'AV1', '  AVC  ')
    for value in values:
        expected = None if value is None else aliases.get(value, value)
        assert sonarr_video_codec(value) == expected


def test_sonarr_video_canonical_encoder_prefixes_precede_suffixes() -> None:
    prefixes = (('XviD', 'XviD'), ('DivX', 'DivX'))
    suffixes = (('VP6', 'VP6'), ('VP7', 'VP7'), ('VP8', 'VP8'), ('VP9', 'VP9'))
    for (prefix, expected), (suffix, _) in product(prefixes, suffixes):
        assert sonarr_video_codec(prefix + ' encoder ' + suffix) == expected


def test_sonarr_video_canonical_suffixes_and_near_misses() -> None:
    for suffix, expected in (('VP6', 'VP6'), ('VP7', 'VP7'), ('VP8', 'VP8'), ('VP9', 'VP9')):
        assert sonarr_video_codec('On2 ' + suffix) == expected
    for value in ('VP5', 'VP10', 'On2 VP9 ', 'VP8x', 'Xvi', 'Div', 'vendorXviD', ' DivX'):
        assert sonarr_video_codec(value) == value


def test_sonarr_preserves_generated_unknown_unicode_whitespace_and_long_names() -> None:
    for value in _unknown_names():
        assert sonarr_audio_codec(value) == value
        assert sonarr_video_codec(value) == value


def test_case_insensitive_sonarr_audio_alias_extensions() -> None:
    aliases = (('AC-3', 'AC3'), ('E-AC-3', 'EAC3'), ('MPEG Audio', 'MP3'))
    for canonical, expected in aliases:
        for variant in _case_variants(canonical):
            assert sonarr_audio_codec(variant) == expected


def test_case_insensitive_sonarr_video_exact_alias_extensions() -> None:
    aliases = (
        ('x264', 'h264'), ('AVC', 'h264'), ('x265', 'h265'), ('HEVC', 'h265'),
        ('MPEG-1 Video', 'Mpeg'), ('MPEG-2 Video', 'Mpeg2'),
        ('MPEG-4 Video', 'Mpeg4'), ('VC-1', 'VC1'),
    )
    for canonical, expected in aliases:
        for variant in _case_variants(canonical):
            assert sonarr_video_codec(variant) == expected


def test_case_insensitive_sonarr_video_prefix_extension_and_precedence() -> None:
    for canonical, expected in (('XviD', 'XviD'), ('DivX', 'DivX')):
        for variant in _case_variants(canonical):
            assert sonarr_video_codec(variant + ' encoder VP9') == expected
            assert sonarr_video_codec(variant + ' encoder VP6') == expected


def test_case_insensitive_sonarr_video_suffix_extensions() -> None:
    for canonical, expected in (('VP6', 'VP6'), ('VP7', 'VP7'), ('VP8', 'VP8'), ('VP9', 'VP9')):
        for variant in _case_variants(canonical):
            assert sonarr_video_codec('On2 ' + variant) == expected


def _case_variants(value: str) -> tuple[str, ...]:
    choices = tuple((character.lower(), character.upper()) if character.isalpha() else (character,)
                    for character in value)
    return tuple(''.join(parts) for parts in product(*choices))


def _unknown_names() -> tuple[str, ...]:
    alphabet = ('q', 'Z', '_', ' ', '\t', '\n', '🚀', 'é', '\u0301', 'К', '音')
    generated = tuple(''.join(parts) for length in (0, 1, 2, 3)
                      for parts in product(alphabet, repeat=length))
    long_values = ('vendor-' * 128, ('音é🚀_' * 64), ('vendor XviD VP9' + 'x' * 512))
    return (*generated, *long_values)
