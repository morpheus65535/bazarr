import json
import subprocess
from os import path
from sys import getfilesystemencoding

import ffprobeparsers


class VideoFileParser:
    def __init__(
        self,
        ffprobe="ffprobe",
        includeMissing=True,
        rawMode=False,
    ):
        self._ffprobe = ffprobe
        self._includeMissing = includeMissing
        self._rawMode = rawMode

    ########################################
    # Main Method

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
            "-v",
            "quiet",
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
        if fOutput["chapters"] is None:
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
        command = [parser] + commandArgs + [inputFile.encode(getfilesystemencoding())]
        try:
            completedProcess = subprocess.check_output(
                command, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            raise IOError(
                "Error occurred during execution - " + e.output
            )
        return completedProcess

    @staticmethod
    def _checkExecutable(executable):
        """Checks if target is executable

        Args:
            executable (str): Executable location, can be file or command

        Raises:
            FileNotFoundError: Executable was not found

        """
        try:
            subprocess.check_output(
                [executable, "--help"],
                stderr=subprocess.STDOUT
            )
        except OSError:
            raise FileNotFoundError(executable + " not found")


class FileNotFoundError(Exception):
    pass


class IOError(Exception):
    pass
