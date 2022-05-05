# coding=utf-8

def RadarrFormatAudioCodec(audioFormat, audioCodecID, audioProfile, audioAdditionalFeatures):
    if type(audioFormat) is not str:
        return audioFormat
    else:
        if audioFormat == "AC-3":
            return "AC3"
        elif audioFormat == "E-AC-3":
            return "EAC3"
        elif audioFormat == "AAC":
            if audioCodecID == "A_AAC/MPEG4/LC/SBR":
                return "HE-AAC"
            else:
                return "AAC"
        elif audioFormat.strip() == "mp3":
            return "MP3"
        elif audioFormat == "MPEG Audio":
            if audioCodecID == "55" or audioCodecID == "A_MPEG/L3" or audioProfile == "Layer 3":
                return "MP3"
            if audioCodecID == "A_MPEG/L2" or audioProfile == "Layer 2":
                return "MP2"
        elif audioFormat == "MLP FBA":
            if audioAdditionalFeatures == "16-ch":
                return "TrueHD Atmos"
            else:
                return "TrueHD"
        else:
            return audioFormat


def RadarrFormatVideoCodec(videoFormat, videoCodecID, videoCodecLibrary):
    if type(videoFormat) is not str:
        return videoFormat
    else:
        if videoFormat == "x264":
            return "h264"
        elif videoFormat == "AVC" or videoFormat == "V.MPEG4/ISO/AVC":
            return "h264"
        elif videoCodecLibrary and (videoFormat == "HEVC" or videoFormat == "V_MPEGH/ISO/HEVC"):
            if videoCodecLibrary.startswith("x265"):
                return "h265"
        elif videoCodecID and videoFormat == "MPEG Video":
            if videoCodecID == "2" or videoCodecID == "V_MPEG2":
                return "Mpeg2"
            else:
                return "Mpeg"
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
        elif videoFormat == "DivX" or videoFormat == "div3":
            return "DivX"
        else:
            return videoFormat
