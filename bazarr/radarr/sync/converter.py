# coding=utf-8

def RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile, audioAdditionalFeatures):
    if type(audioFormat) is not str:
        return audioFormat
    if audioFormat == "AC-3":
        return "AC3"
    elif audioFormat == "E-AC-3":
        return "EAC3"
    elif audioFormat == "AAC":
        return "HE-AAC" if audioCodecID == "A_AAC/MPEG4/LC/SBR" else "AAC"
    elif audioFormat.strip() == "mp3":
        return "MP3"
    elif audioFormat == "MPEG Audio":
        if audioCodecID == "55" or audioCodecID == "A_MPEG/L3" or audioProfile == "Layer 3":
            return "MP3"
        if audioCodecID == "A_MPEG/L2" or audioProfile == "Layer 2":
            return "MP2"
    elif audioFormat == "MLP FBA":
        return "TrueHD Atmos" if audioAdditionalFeatures == "16-ch" else "TrueHD"
    else:
        return audioFormat


def RadarrFormatVideoCodec(videoFormat, videoCodecID, videoCodecLibrary):
    if type(videoFormat) is not str:
        return videoFormat
    if videoFormat == "x264":
        return "h264"
    elif videoFormat in ["AVC", "V.MPEG4/ISO/AVC"]:
        return "h264"
    elif videoCodecLibrary and videoFormat in ["HEVC", "V_MPEGH/ISO/HEVC"]:
        if videoCodecLibrary.startswith("x265"):
            return "h265"
    elif videoCodecID and videoFormat == "MPEG Video":
        return "Mpeg2" if videoCodecID in ["2", "V_MPEG2"] else "Mpeg"
    elif videoFormat == "MPEG-1 Video":
        return "Mpeg"
    elif videoFormat == "MPEG-2 Video":
        return "Mpeg2"
    elif videoCodecLibrary and videoCodecID and videoFormat == "MPEG-4 Visual":
        if videoCodecID.endswith("XVID") or videoCodecLibrary.startswith("XviD"):
            return "XviD"
        if videoCodecID.endswith("DIV3") or videoCodecID.endswith("DIVX") or videoCodecID.endswith(
                "DX50") or videoCodecLibrary.startswith("DivX"):
            return "DivX"
    elif videoFormat == "VC-1":
        return "VC1"
    elif videoFormat == "WMV2":
        return "WMV"
    elif videoFormat in ["DivX", "div3"]:
        return "DivX"
    else:
        return videoFormat
