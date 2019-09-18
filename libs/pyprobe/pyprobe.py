import json
import subprocess
import xml.etree
import xml.etree.ElementTree
from io import StringIO
from os import path
import re

from pyprobe import ffprobeparsers, mediainfoparsers


class VideoFileParser:
    def __init__(
        self,
        ffprobe="ffprobe",
        mediainfo="mediainfo",
        includeMissing=True,
        rawMode=False,
    ):
        self._ffprobe = ffprobe
        self._mediainfo = mediainfo
        self._includeMissing = includeMissing
        self._rawMode = rawMode

    ########################################
    # Main Method

    def parseMediainfo(self, inputFile):
        """Takes an input file and returns the parsed data using mediainfo.
        
        Args:
            inputFile (str): Video file path

        Returns:
            dict<str, dict<str, var>>: Parsed video info

        Raises:
            FileNotFoundError: The input video file or input executable was not found
            IOError: Execution failed

        """
        if not path.isfile(inputFile):
            raise FileNotFoundError(inputFile + " not found")
        self._checkExecutable(self._mediainfo)
        self._checkMediainfoVersion(self._mediainfo)
        xmlData = self._executeMediainfo(inputFile)
        return self._parseMediainfo(xmlData, inputFile)

    def parseFfprobe(self, inputFile):
        """Takes an input file and returns the parsed data using ffprobe.
        
        Args:
            inputFile (str): Video file path

        Returns:
            dict<str, dict<str, var>>: Parsed video info

        Raises:
            FileNotFoundError: The input video file or input executable was not found
            IOError: Execution failed

        """
        if not path.isfile(inputFile):
            raise FileNotFoundError(inputFile + " not found")
        self._checkExecutable(self._ffprobe)
        fdict = self._executeFfprobe(inputFile)
        return self._parseFfprobe(fdict, inputFile)

    ########################################
    # Mediainfo Parsing

    def _executeMediainfo(self, inputFile):
        """Executes mediainfo program on input file to get raw info

        Args:
            inputFile (str): Video file path

        Returns:
            xml.ElementTree.etree: Mediainfo output

        Raises:
            IOError: Mediainfo output could not be parsed as XML data

        """
        commandArgs = ["-f", "--Language=raw", "--Output=XML"]
        outputXml = self._executeParser(self._mediainfo, commandArgs, inputFile)
        try:
            xmlRoot = self._decodeMediainfoOutput(outputXml)
        except xml.etree.ElementTree.ParseError:
            raise IOError("Could not decode mediainfo output for file " + inputFile)
        return xmlRoot

    def _parseMediainfo(self, xmlRoot, inputFile):
        """Parse mediainfo output into an organized data structure

        Args:
            xmlRoot (xml.ElementTree.etree): Mediainfo output
            inputFile (str): Video file path

        Returns:
            dict<str, dict<str, var>>: Parsed video data

        """
        videoInfo = {}
        videoInfo["path"] = path.abspath(inputFile)
        videoInfo.update(
            mediainfoparsers.RootParser.parse(
                xmlRoot.find(".//track[@type='General']"),
                self._rawMode,
                self._includeMissing,
            )
        )
        videoInfo.update(self._parseMediainfoStreams(xmlRoot))
        videoInfo.update(self._parseMediainfoChapters(xmlRoot, videoInfo["duration"]))
        return videoInfo

    @staticmethod
    def _decodeMediainfoOutput(xmlData):
        # Strip namespaces from xml string
        # Code used from https://stackoverflow.com/a/25920989
        it = xml.etree.ElementTree.iterparse(StringIO(xmlData))
        for _, el in it:
            if "}" in el.tag:
                el.tag = el.tag.split("}", 1)[1]
        return it.root

    def _parseMediainfoStreams(self, xmlData):
        """Parses video, audio, and subtitle streams
        
        Args:
            xmlData (dict): Stream data from mediainfo

        Returns:
            dict<str, dict<str, var>>: Parsed streams - video, audio, and subtitle

        """
        parsedInfo = {"videos": [], "audios": [], "subtitles": []}
        for stream in xmlData.findall(".//track"):
            streamType = stream.attrib["type"]
            if streamType == "Video":
                parsedInfo["videos"].append(
                    mediainfoparsers.VideoStreamParser.parse(
                        stream, self._rawMode, self._includeMissing
                    )
                )
            elif streamType == "Audio":
                parsedInfo["audios"].append(
                    mediainfoparsers.AudioStreamParser.parse(
                        stream, self._rawMode, self._includeMissing
                    )
                )
            elif streamType == "Text":
                parsedInfo["subtitles"].append(
                    mediainfoparsers.SubtitleStreamParser.parse(
                        stream, self._rawMode, self._includeMissing
                    )
                )
        return parsedInfo

    def _parseMediainfoChapters(self, xmlData, duration):
        """Since mediainfo does not give end times for each chapter,
        start times for the following chapter are added to the previous chapter.

        Args:
            xmlData (dict): Stream data from mediainfo
            duration (int): Video duration

        Returns:
            dict<str, dict<str, var>>: Parsed chapters
        
        """
        parsedInfo = {"chapters": []}
        for extra in xmlData.find(".//track[@type='Menu']/extra"):
            match = re.fullmatch(r"_\d*_\d\d_\d\d_\d\d\d", extra.tag)
            if match:
                parsedInfo["chapters"].append(
                    mediainfoparsers.ChapterParser.parse(
                        extra, self._rawMode, self._includeMissing
                    )
                )
        if not self._rawMode:
            mediainfoparsers.ChapterParser.addEndTimes(parsedInfo["chapters"], duration)
        return parsedInfo

    ########################################
    # ffprobe Parsing

    def _executeFfprobe(self, inputFile):
        """Executes ffprobe program on input file to get raw info

        fdict = dict<str, fdict> or dict<str, str>

        Args:
            inputFile (str): Video file path

        Returns:
            fdict: Parsed data

        """
        commandArgs = [
            "-hide_banner",
            "-show_error",
            "-show_format",
            "-show_streams",
            "-show_programs",
            "-show_chapters",
            "-show_private_data",
            "-print_format",
            "json",
        ]
        outputJson = self._executeParser(self._ffprobe, commandArgs, inputFile)

        try:
            data = json.loads(outputJson)
        except json.JSONDecodeError:
            raise IOError("Could not decode ffprobe output for file " + inputFile)
        return data

    def _parseFfprobe(self, fOutput, inputFile):
        """Parse all data from fOutput to organized format

        fdict = dict<str, fdict> or dict<str, str>

        Args:
            fOutput (fdict): Stream data from ffprobe
            inputFile (str): Video file path

        Returns:
            dict<str, dict<str, str>>: Parsed video data

        """
        videoInfo = {}
        videoInfo["path"] = path.abspath(inputFile)
        videoInfo.update(
            ffprobeparsers.RootParser.parse(
                fOutput["format"], self._rawMode, self._includeMissing
            )
        )
        videoInfo.update(self._parseFfprobeStreams(fOutput))
        videoInfo.update(self._parseFfprobeChapters(fOutput))
        if not self._rawMode:
            ffprobeparsers.ChapterParser.fillEmptyTitles(videoInfo["chapters"])
        return videoInfo

    def _parseFfprobeStreams(self, fOutput):
        """Parses video, audio, and subtitle streams
        
        fdict = dict<str, fdict> or dict<str, str>

        Args:
            streams_data (fdict): Stream data from ffprobe

        Returns:
            dict<str, dict<str, var>>: Parsed streams - video, audio, and subtitle

        """
        parsedInfo = {"videos": [], "audios": [], "subtitles": []}
        for stream in fOutput["streams"]:
            streamType = stream["codec_type"]
            data = None
            if streamType == "video":
                data = ffprobeparsers.VideoStreamParser.parse(
                    stream, self._rawMode, self._includeMissing
                )
                parsedInfo["videos"].append(data)
            elif streamType == "audio":
                data = ffprobeparsers.AudioStreamParser.parse(
                    stream, self._rawMode, self._includeMissing
                )
                parsedInfo["audios"].append(data)
            elif streamType == "subtitle":
                data = ffprobeparsers.SubtitleStreamParser.parse(
                    stream, self._rawMode, self._includeMissing
                )
                parsedInfo["subtitles"].append(data)
        return parsedInfo

    def _parseFfprobeChapters(self, fOutput):
        """Parses chapters
        
        fdict = dict<str, fdict> or dict<str, str>

        Args:
            chapters_data (fdict): Stream data from ffprobe

        Returns:
            dict<str, dict<str, var>>: Parsed chapters

        """
        parsedInfo = {"chapters": []}
        if fOutput["chapters"] == None:
            return parsedInfo
        for chapter in fOutput["chapters"]:
            parsedInfo["chapters"].append(
                ffprobeparsers.ChapterParser.parse(
                    chapter, self._rawMode, self._includeMissing
                )
            )
        return parsedInfo

    ########################################
    # Misc Methods

    @staticmethod
    def _executeParser(parser, commandArgs, inputFile):
        """Executes parser on the input file

        Args:
            parser (str): Executable location or command
            commandArgs (list of strings): Extra command arguments
            inputFile (str): the input file location

        Raises:
            IOError: ffprobe execution failed

        """
        command = [parser] + commandArgs + [inputFile]
        completedProcess = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
        )
        if completedProcess.returncode != 0:
            raise IOError(
                "Error occurred during execution - " + completedProcess.stderr
            )
        return completedProcess.stdout

    @staticmethod
    def _checkExecutable(executable):
        """Checks if target is executable

        Args:
            executable (str): Executable location, can be file or command

        Raises:
            FileNotFoundError: Executable was not found

        """
        try:
            subprocess.run(
                [executable, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            raise FileNotFoundError(executable + " not found")

    @staticmethod
    def _checkMediainfoVersion(executable):
        """Checks if the Mediainfo version is >=17.10
        In the version jump from 0.7.97 to 17.10 came lots of changes
          to the way Mediainfo outputs data. Therefore, this will
          only support versions >=17.10.
        
        Some linux software repositories still distribute old
          versions of mediainfo, so the user must install
          using packages from mediainfo's website.
          
        """
        command = [executable, "--version"]
        completedProcess = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
        )
        match = re.search(r"v\d*(\.\d*)*", completedProcess.stdout)
        version = match.group()[1:]
        if version.split(".")[0] == "0":
            raise IOError("Mediainfo version is <17.10 - (v" + version + ")")
