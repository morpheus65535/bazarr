# coding=utf-8

import re

WordDelimiterRegex = re.compile(r"(\s|\.|,|_|-|=|\|)+")
PunctuationRegex = re.compile(r"[^\w\s]")
CommonWordRegex = re.compile(r"\b(a|an|the|and|or|of)\b\s?")
DuplicateSpacesRegex = re.compile(r"\s{2,}")


def normalize_title(title):
    title = title.lower()

    title = re.sub(WordDelimiterRegex, " ", title)
    title = re.sub(PunctuationRegex, "", title)
    title = re.sub(CommonWordRegex, "", title)
    title = re.sub(DuplicateSpacesRegex, " ", title)

    return title.strip()


VIDEO_EXTENSION = [
    # Unknown
    ".webm",

    # SDTV
    ".m4v",
    ".3gp",
    ".nsv",
    ".ty",
    ".strm",
    ".rm",
    ".rmvb",
    ".m3u",
    ".ifo",
    ".mov",
    ".qt",
    ".divx",
    ".xvid",
    ".bivx",
    ".nrg",
    ".pva",
    ".wmv",
    ".asf",
    ".asx",
    ".ogm",
    ".ogv",
    ".m2v",
    ".avi",
    ".bin",
    ".dat",
    ".dvr-ms",
    ".mpg",
    ".mpeg",
    ".mp4",
    ".avc",
    ".vp3",
    ".svq3",
    ".nuv",
    ".viv",
    ".dv",
    ".fli",
    ".flv",
    ".wpl",

    # HD
    ".mkv",
    ".mk3d",
    ".ts",
    ".wtv",

    # Bluray
    ".m2ts",
]
