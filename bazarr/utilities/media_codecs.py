# coding=utf-8

from collections.abc import Callable
from typing import TypeAlias

_AUDIO_ALIASES: dict[str, str] = {
    'ac-3': 'AC3',
    'e-ac-3': 'EAC3',
    'mpeg audio': 'MP3',
}

_VIDEO_ALIASES: dict[str, str] = {
    'x264': 'h264',
    'avc': 'h264',
    'mpeg-1 video': 'Mpeg',
    'mpeg-2 video': 'Mpeg2',
    'vc-1': 'VC1',
}

_RADARR_VIDEO_ALIASES = _VIDEO_ALIASES | {
    'v.mpeg4/iso/avc': 'h264',
    'wmv2': 'WMV',
    'divx': 'DivX',
    'div3': 'DivX',
}
_SONARR_VIDEO_ALIASES = _VIDEO_ALIASES | {'x265': 'h265', 'hevc': 'h265', 'mpeg-4 video': 'Mpeg4'}
_VIDEO_ENCODERS = (('XviD', 'xvid', ('xvid',)), ('DivX', 'divx', ('div3', 'divx', 'dx50')))
_VIDEO_SUFFIXES = {'vp6': 'VP6', 'vp7': 'VP7', 'vp8': 'VP8', 'vp9': 'VP9'}
_MPEG_AUDIO_LAYERS = (('MP3', ('55', 'a_mpeg/l3'), 'layer 3'), ('MP2', ('a_mpeg/l2',), 'layer 2'))


def _aac(codec_id: str | None, _profile: str | None, _features: str | None) -> str:
    return 'HE-AAC' if (codec_id or '').casefold() == 'a_aac/mpeg4/lc/sbr' else 'AAC'


def _mpeg_audio(codec_id: str | None, profile: str | None, _features: str | None) -> str | None:
    identifier, profile_key = (codec_id or '').casefold(), (profile or '').casefold()
    for canonical, identifiers, layer in _MPEG_AUDIO_LAYERS:
        if identifier in identifiers or profile_key == layer:
            return canonical
    return None


def _truehd(_codec_id: str | None, _profile: str | None, features: str | None) -> str:
    return 'TrueHD Atmos' if (features or '').casefold() == '16-ch' else 'TrueHD'


def _video_encoder(identifier: str, library: str) -> str | None:
    for canonical, prefix, suffixes in _VIDEO_ENCODERS:
        if identifier.endswith(suffixes) or library.startswith(prefix):
            return canonical
    return None


def _hevc(codec: str | None, _codec_id: str | None, library: str | None) -> str | None:
    if not library:
        return codec
    return 'h265' if library.casefold().startswith('x265') else None


def _mpeg_video(codec: str | None, codec_id: str | None, _library: str | None) -> str | None:
    if not codec_id:
        return codec
    return 'Mpeg2' if codec_id.casefold() in ('2', 'v_mpeg2') else 'Mpeg'


def _mpeg4_video(codec: str | None, codec_id: str | None, library: str | None) -> str | None:
    if not codec_id or not library:
        return codec
    return _video_encoder(codec_id.casefold(), library.casefold())


_CodecHandler: TypeAlias = Callable[[str | None, str | None, str | None], str | None]
_RADARR_AUDIO_HANDLERS: dict[str, _CodecHandler] = {'aac': _aac, 'mpeg audio': _mpeg_audio, 'mlp fba': _truehd}
_RADARR_VIDEO_HANDLERS: dict[str, _CodecHandler] = {
    'hevc': _hevc, 'v_mpegh/iso/hevc': _hevc, 'mpeg video': _mpeg_video, 'mpeg-4 visual': _mpeg4_video,
}


def radarr_audio_codec(codec: str | None, codec_id: str | None, profile: str | None,
                       features: str | None) -> str | None:
    key = (codec or '').casefold()
    if key.strip() == 'mp3':
        return 'MP3'
    handler = _RADARR_AUDIO_HANDLERS.get(key)
    return handler(codec_id, profile, features) if handler is not None else _AUDIO_ALIASES.get(key, codec)


def radarr_video_codec(codec: str | None, codec_id: str | None, codec_library: str | None) -> str | None:
    key = (codec or '').casefold()
    handler = _RADARR_VIDEO_HANDLERS.get(key)
    return handler(codec, codec_id, codec_library) if handler is not None else _RADARR_VIDEO_ALIASES.get(key, codec)


def sonarr_audio_codec(codec: str | None) -> str | None:
    return _AUDIO_ALIASES.get((codec or '').casefold(), codec)


def sonarr_video_codec(codec: str | None) -> str | None:
    key = (codec or '').casefold()
    encoder = _video_encoder('', key)
    return encoder if encoder is not None else _VIDEO_SUFFIXES.get(key[-3:], _SONARR_VIDEO_ALIASES.get(key, codec))
