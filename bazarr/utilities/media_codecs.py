# coding=utf-8

from functools import lru_cache

_AUDIO_ALIASES = {'ac-3': 'AC3', 'e-ac-3': 'EAC3', 'mpeg audio': 'MP3'}
_VIDEO_ALIASES = {
    'x264': 'h264', 'avc': 'h264', 'mpeg-1 video': 'Mpeg', 'mpeg-2 video': 'Mpeg2', 'vc-1': 'VC1',
}
_RADARR_VIDEO_ALIASES = _VIDEO_ALIASES | {
    'v.mpeg4/iso/avc': 'h264', 'wmv2': 'WMV', 'divx': 'DivX', 'div3': 'DivX',
}
_SONARR_VIDEO_ALIASES = _VIDEO_ALIASES | {'x265': 'h265', 'hevc': 'h265', 'mpeg-4 video': 'Mpeg4'}
_VIDEO_SUFFIXES = {'vp6': 'VP6', 'vp7': 'VP7', 'vp8': 'VP8', 'vp9': 'VP9'}
_MPEG_IDS = {'55': 'MP3', 'a_mpeg/l3': 'MP3', 'a_mpeg/l2': 'MP2'}
_MPEG_PROFILES = {'layer 3': 'MP3', 'layer 2': 'MP2'}


# Labels and encoder metadata repeat across files. Bound the retained combinations.
@lru_cache(maxsize=128)
def radarr_audio_codec(codec: str | None, codec_id: str | None, profile: str | None,
                       features: str | None) -> str | None:
    key = (codec or '').casefold()
    if key == 'aac':
        return 'HE-AAC' if (codec_id or '').casefold() == 'a_aac/mpeg4/lc/sbr' else 'AAC'
    if key == 'mpeg audio':
        identifier = _MPEG_IDS.get((codec_id or '').casefold())
        layer = _MPEG_PROFILES.get((profile or '').casefold())
        return 'MP3' if identifier == 'MP3' or layer == 'MP3' else identifier or layer
    if key == 'mlp fba':
        return 'TrueHD Atmos' if (features or '').casefold() == '16-ch' else 'TrueHD'
    return 'MP3' if key.strip() == 'mp3' else _AUDIO_ALIASES.get(key, codec)


@lru_cache(maxsize=128)
def radarr_video_codec(codec: str | None, codec_id: str | None, codec_library: str | None) -> str | None:
    key = (codec or '').casefold()
    if key in ('hevc', 'v_mpegh/iso/hevc'):
        return ('h265' if codec_library.casefold().startswith('x265') else None) if codec_library else codec
    if key == 'mpeg video':
        return ('Mpeg2' if codec_id.casefold() in ('2', 'v_mpeg2') else 'Mpeg') if codec_id else codec
    if key == 'mpeg-4 visual':
        if not codec_id or not codec_library:
            return codec
        identifier, library = codec_id.casefold(), codec_library.casefold()
        if identifier.endswith('xvid') or library.startswith('xvid'):
            return 'XviD'
        return 'DivX' if identifier.endswith(('div3', 'divx', 'dx50')) or library.startswith('divx') else None
    return _RADARR_VIDEO_ALIASES.get(key, codec)


def sonarr_audio_codec(codec: str | None) -> str | None:
    return _AUDIO_ALIASES.get((codec or '').casefold(), codec)


def sonarr_video_codec(codec: str | None) -> str | None:
    key = (codec or '').casefold()
    if key.startswith('xvid'):
        return 'XviD'
    if key.startswith('divx'):
        return 'DivX'
    return _VIDEO_SUFFIXES.get(key[-3:], _SONARR_VIDEO_ALIASES.get(key, codec))


@lru_cache(maxsize=128)
def sonarr_codecs(audio: str | None, video: str | None) -> tuple[str | None, str | None]:
    return sonarr_audio_codec(audio), sonarr_video_codec(video)
