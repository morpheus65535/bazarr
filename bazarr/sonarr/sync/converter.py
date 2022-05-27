# coding=utf-8


def SonarrFormatAudioCodec(audio_codec):
    if type(audio_codec) is not str:
        return audio_codec
    if audio_codec == "AC-3":
        return "AC3"
    elif audio_codec == "E-AC-3":
        return "EAC3"
    elif audio_codec == "MPEG Audio":
        return "MP3"
    else:
        return audio_codec


def SonarrFormatVideoCodec(video_codec):
    if type(video_codec) is not str:
        return video_codec
    if video_codec in ["x264", "AVC"]:
        return "h264"
    elif video_codec in ["x265", "HEVC"]:
        return "h265"
    elif video_codec.startswith("XviD"):
        return "XviD"
    elif video_codec.startswith("DivX"):
        return "DivX"
    elif video_codec == "MPEG-1 Video":
        return "Mpeg"
    elif video_codec == "MPEG-2 Video":
        return "Mpeg2"
    elif video_codec == "MPEG-4 Video":
        return "Mpeg4"
    elif video_codec == "VC-1":
        return "VC1"
    elif video_codec.endswith("VP6"):
        return "VP6"
    elif video_codec.endswith("VP7"):
        return "VP7"
    elif video_codec.endswith("VP8"):
        return "VP8"
    elif video_codec.endswith("VP9"):
        return "VP9"
    else:
        return video_codec
