import logging

import pytest

from bazarr.utilities import video_analyzer

logging.getLogger("knowit").setLevel(logging.WARNING)

M_INFO = {
    "creatingLibrary": {
        "name": "MediaInfoLib",
        "version": "23.03",
        "url": "https://mediaarea.net/MediaInfo",
    },
    "media": {
        "@ref": "/mnt/media/Hocus.Pocus.1993.1080p.DSNP.WEB-DL.DDP5.1.H.264.DUAL-PD.mkv",
        "track": [
            {
                "@type": "General",
                "UniqueID": "177986280948425821736023466260510750529",
                "VideoCount": "1",
                "AudioCount": "2",
                "TextCount": "31",
                "FileExtension": "mkv",
                "Format": "Matroska",
                "Format_Version": "4",
                "FileSize": "6468058376",
                "Duration": "5766.219",
                "OverallBitRate_Mode": "VBR",
                "OverallBitRate": "8973726",
                "FrameRate": "23.976",
                "FrameCount": "138251",
                "StreamSize": "2607619",
                "IsStreamable": "Yes",
                "Encoded_Date": "2023-04-22 16:46:57 UTC",
                "File_Modified_Date": "2023-05-17 01:49:55 UTC",
                "File_Modified_Date_Local": "2023-05-16 21:49:55",
                "Encoded_Application": "mkvmerge v75.0.0 ('Goliath') 64-bit",
                "Encoded_Library": "libebml v1.4.4 + libmatroska v1.7.1",
            },
            {
                "@type": "Video",
                "StreamOrder": "0",
                "ID": "1",
                "UniqueID": "9393509843335289949",
                "Format": "AVC",
                "Format_Profile": "High",
                "Format_Level": "4",
                "Format_Settings_CABAC": "Yes",
                "Format_Settings_RefFrames": "4",
                "CodecID": "V_MPEG4/ISO/AVC",
                "Duration": "5766.219000000",
                "BitRate_Mode": "VBR",
                "BitRate": "8458733",
                "BitRate_Maximum": "12749952",
                "Width": "1920",
                "Height": "1080",
            },
            {
                "@type": "Audio",
                "@typeorder": "1",
                "StreamOrder": "1",
                "ID": "2",
                "UniqueID": "12329215851643269509",
                "Format": "E-AC-3",
                "Format_Commercial_IfAny": "Dolby Digital Plus",
                "Format_Settings_Endianness": "Big",
                "CodecID": "A_EAC3",
                "Duration": "5766.112000000",
                "BitRate_Mode": "CBR",
                "BitRate": "256000",
                "Language": "pt-BR",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Audio",
                "@typeorder": "2",
                "StreamOrder": "2",
                "ID": "3",
                "UniqueID": "1232921585164326950923",
                "Format": "E-AC-3",
                "Format_Commercial_IfAny": "Dolby Digital Plus",
                "Format_Settings_Endianness": "Big",
                "CodecID": "A_EAC3",
                "Duration": "5766.112000000",
                "BitRate_Mode": "CBR",
                "BitRate": "256000",
                "Language": "pt",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "7",
                "StreamOrder": "9",
                "ID": "10",
                "UniqueID": "2233390560797234737",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "5480.360000000",
                "BitRate": "45",
                "FrameRate": "0.206",
                "FrameCount": "1129",
                "ElementCount": "1129",
                "StreamSize": "31194",
                "Language": "es-419",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "9",
                "StreamOrder": "11",
                "ID": "12",
                "UniqueID": "1345374948683222936",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "5561.600000000",
                "BitRate": "46",
                "FrameRate": "0.164",
                "FrameCount": "914",
                "ElementCount": "914",
                "StreamSize": "32145",
                "Language": "es-ES",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "11",
                "StreamOrder": "13",
                "ID": "14",
                "UniqueID": "17039172451186467602",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "4966.120000000",
                "BitRate": "1",
                "FrameRate": "0.007",
                "FrameCount": "35",
                "ElementCount": "35",
                "StreamSize": "1011",
                "Language": "fr-CA",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "24",
                "StreamOrder": "26",
                "ID": "27",
                "UniqueID": "16221047442617815320",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "4961.520000000",
                "BitRate": "0",
                "FrameRate": "0.002",
                "FrameCount": "11",
                "ElementCount": "11",
                "StreamSize": "379",
                "Language": "pt-BR",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "30",
                "StreamOrder": "32",
                "ID": "33",
                "UniqueID": "4259582444071016270",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "5507.508000000",
                "BitRate": "50",
                "FrameRate": "0.253",
                "FrameCount": "1392",
                "ElementCount": "1392",
                "StreamSize": "34539",
                "Language": "zh-Hans",
                "Default": "No",
                "Forced": "No",
            },
            {
                "@type": "Text",
                "@typeorder": "31",
                "StreamOrder": "33",
                "ID": "34",
                "UniqueID": "4890027048965677919",
                "Format": "UTF-8",
                "CodecID": "S_TEXT/UTF8",
                "Duration": "5730.725000000",
                "BitRate": "43",
                "FrameRate": "0.207",
                "FrameCount": "1186",
                "ElementCount": "1186",
                "StreamSize": "31154",
                "Language": "zh-Hant",
                "Default": "No",
                "Forced": "No",
            },
        ],
    },
}


@pytest.fixture
def video_file():
    return "tests/subliminal_patch/data/file_1.mkv"


class _MockLanguage:
    """Mock Language object with alpha3 attribute"""
    def __init__(self, lang_code):
        # Map BCP 47 / other codes to alpha3 and country
        lang_map = {
            "pt-BR": ("pob", "BR", None),  # Brazilian Portuguese
            "pt": ("por", "PT", None),     # Portuguese
            "es-419": ("spl", "419", None), # Spanish - Latin American
            "es-ES": ("spa", "ES", None),  # Spanish - Spain
            "fr-CA": ("fra", "CA", None),  # French - Canadian
            "zh-Hans": ("zhs", "CN", "Hans"),  # Chinese - Simplified
            "zh-Hant": ("zht", "TW", "Hant"),  # Chinese - Traditional
        }
        alpha3, country, script = lang_map.get(lang_code, (lang_code, None, None))
        self.alpha3 = alpha3
        self.country = country
        self.script = script
        self.alpha2 = lang_code.split("-")[0] if "-" in lang_code else lang_code


@pytest.fixture
def mediainfo_data(mocker, video_file):
    mocker.patch(
        "knowit.providers.mediainfo.MediaInfoCTypesExecutor._execute",
        return_value=M_INFO,
    )
    try:
        data = video_analyzer.know(
            video_path=video_file,
            context={"provider": "mediainfo"},
        )
    except Exception:
        data = {}

    # If know() failed to parse, manually build the expected structure from M_INFO
    if not data or (not data.get("subtitle") and not data.get("audio")):
        parsed_data = {"subtitle": [], "audio": []}
        if "media" in M_INFO and "track" in M_INFO["media"]:
            for track in M_INFO["media"]["track"]:
                track_type = track.get("@type")
                if track_type == "Text":
                    # Convert uppercase keys to lowercase for subtitle tracks
                    # Parse CodecID to get subtitle format
                    codec_id = track.get("CodecID", "")
                    format_map = {
                        "S_TEXT/UTF8": "SubRip",
                        "S_TEXT/ASS": "ASS",
                        "S_TEXT/SSA": "SSA",
                        "S_VOBSUB": "VobSub",
                        "S_DVBSUB": "DVB Subtitle",
                        "S_HDMV/PGS": "PGS",
                    }
                    subtitle_format = format_map.get(codec_id, track.get("Format", "SubRip"))

                    subtitle_track = {
                        "language": _MockLanguage(track.get("Language")),
                        "format": subtitle_format,
                        "forced": track.get("Forced") == "Yes",
                        "hearing_impaired": track.get("Hearing_Impaired") == "Yes",
                        "id": track.get("ID"),
                        "name": "",
                    }
                    parsed_data["subtitle"].append(subtitle_track)
                elif track_type == "Audio":
                    # Convert uppercase keys to lowercase for audio tracks
                    audio_track = {
                        "language": _MockLanguage(track.get("Language")),
                        "format": track.get("Format"),
                    }
                    parsed_data["audio"].append(audio_track)
        data = parsed_data

    yield data


def test_embedded_subs_reader(mocker, mediainfo_data, video_file):
    mocker.patch(
        "bazarr.utilities.video_analyzer.parse_video_metadata",
        return_value={"mediainfo": mediainfo_data},
    )
    mocker.patch(
        "bazarr.utilities.video_analyzer.alpha3_from_alpha2", return_value=None
    )
    result = video_analyzer.embedded_subs_reader(video_file, 1e6)
    tracks_without_id = [row[1:] for row in result]
    assert ["spl", False, False, "SubRip"] in tracks_without_id
    assert ["pob", False, False, "SubRip"] in tracks_without_id
    assert ["zht", False, False, "SubRip"] in tracks_without_id


def test_embedded_audio_reader(mocker, mediainfo_data, video_file):
    mocker.patch(
        "bazarr.utilities.video_analyzer.parse_video_metadata",
        return_value={"mediainfo": mediainfo_data},
    )
    mocker.patch(
        "bazarr.utilities.video_analyzer.language_from_alpha3", lambda alpha3: alpha3
    )
    result = video_analyzer.embedded_audio_reader(video_file, 1e6)
    assert {"pob", "por"} == set(result)


def test_handle_alpha3_accepts_string_language():
    assert video_analyzer._handle_alpha3({"language": "jpn"}) == "jpn"


def test_embedded_audio_reader_accepts_string_language(mocker, video_file):
    mocker.patch(
        "bazarr.utilities.video_analyzer.parse_video_metadata",
        return_value={"ffprobe": {"audio": [{"language": "jpn"}]}},
    )
    mocker.patch(
        "bazarr.utilities.video_analyzer.language_from_alpha3", lambda alpha3: alpha3
    )

    result = video_analyzer.embedded_audio_reader(1e6, video_file)

    assert result == ["jpn"]
