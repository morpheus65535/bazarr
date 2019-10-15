from os import path

from baseparser import BaseParser


class StreamParser(BaseParser):
    @staticmethod
    def value_codec(data):
        """Returns a string"""
        info = data.get("codec_name", None)
        return info, (info or "null")

    @staticmethod
    def value_format(data):
        """Returns a string"""
        info = data.get("format_name", None)
        return info, (info or "null")

    @staticmethod
    def value_bit_rate(data):
        """Returns an int"""
        info = data.get("bit_rate", None)
        try:
            return info, int(float(info))
        except (ValueError, TypeError):
            return info, 0


class VideoStreamParser(BaseParser):
    @staticmethod
    def value_codec(data):
        return StreamParser.value_codec(data)

    @staticmethod
    def value_format(data):
        return StreamParser.value_format(data)

    @staticmethod
    def value_bit_rate(data):
        return StreamParser.value_bit_rate(data)

    @staticmethod
    def value_resolution(data):
        """Returns a tuple (width, height)"""
        width = data.get("width", None)
        height = data.get("height", None)
        if width is None and height is None:
            return None, (0, 0)
        try:
            return (width, height), (int(float(width)), int(float(height)))
        except (ValueError, TypeError):
            return (width, height), (0, 0)

    @staticmethod
    def average_framerate(data):
        """Returns an int"""
        frames = data.get("nb_frames", None)
        duration = data.get("duration", None)
        try:
            return float(frames) / float(duration)
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0

    @classmethod
    def value_framerate(cls, data):
        """Returns a float"""
        input_str = data.get("avg_frame_rate", None)
        try:
            num, den = input_str.split("/")
            return input_str, round(float(num) / float(den), 3)
        except (ValueError, ZeroDivisionError, AttributeError):
            info = cls.average_framerate(data)
            return input_str, info

    @staticmethod
    def value_aspect_ratio(data):
        """Returns a string"""
        info = data.get("display_aspect_ratio", None)
        return info, (info or "null")

    @staticmethod
    def value_pixel_format(data):
        """Returns a string"""
        info = data.get("pix_fmt", None)
        return info, (info or "null")


class AudioStreamParser(StreamParser):
    @staticmethod
    def value_sample_rate(data):
        """Returns an int - audio sample rate in Hz"""
        info = data.get("sample_rate", None)
        try:
            return info, int(float(info))
        except (ValueError, TypeError):
            return info, 0

    @staticmethod
    def value_channel_count(data):
        """Returns an int"""
        info = data.get("channels", None)
        try:
            return info, int(float(info))
        except (ValueError, TypeError):
            return info, 0

    @staticmethod
    def value_channel_layout(data):
        """Returns a string"""
        info = data.get("channel_layout", None)
        return info, (info or "null")


class SubtitleStreamParser(BaseParser):
    @staticmethod
    def value_codec(data):
        return StreamParser.value_codec(data)

    @staticmethod
    def value_language(data):
        """Returns a string """
        tags = data.get("tags", None)
        if tags:
            info = tags.get("language", None) or tags.get("LANGUAGE", None)
            return info, (info or "null")
        return None, "null"

    @staticmethod
    def value_forced(data):
        """Returns a bool """
        disposition = data.get("disposition", None)
        if disposition:
            info = disposition.get("forced", None)
            return bool(info), (bool(info) or False)
        return None, "null"


class ChapterParser(BaseParser):
    @staticmethod
    def value_start(data):
        """Returns an int"""
        info = data.get("start_time", None)
        try:
            return info, float(data.get("start_time"))
        except (ValueError, TypeError):
            return info, 0

    @classmethod
    def value_end(cls, data):
        """Returns a float"""
        info = data.get("end_time", None)
        try:
            return info, float(info)
        except (ValueError, TypeError):
            return info, 0

    @staticmethod
    def value_title(data):
        """Returns a string"""
        info = data.get("tags", {}).get("title", None)
        return info, (info or "null")

    @staticmethod
    def fillEmptyTitles(chapters):
        """Add text in place of empty titles
        If a chapter doesn't have a title, this will add a basic
        string in the form "Chapter `index+1`"
        
        Args:
            chapters(list<dict>): The list of parsed chapters

        """
        index = 0
        for chapter in chapters:
            if not chapter["title"]:
                chapter["title"] = "Chapter " + str(index)
            index += 1


class RootParser(BaseParser):
    @staticmethod
    def value_duration(data):
        """Returns an int"""
        info = data.get("duration", None)
        try:
            return info, float(info)
        except (ValueError, TypeError):
            return info, 0.0

    @staticmethod
    def value_size(data):
        """Returns an int"""
        info = data.get("size", None)
        if info is None:
            file_path = data.get("filename", "")
            if path.isfile(file_path):
                info = str(path.getsize(file_path))
        try:
            return info, int(float(info))
        except (ValueError, TypeError):
            return info, 0

    @classmethod
    def value_bit_rate(cls, data):
        """Returns an int"""
        info = data.get("bit_rate", None)
        if info is None:
            _, size = cls.value_size(data)
            _, duration = cls.value_duration(data)
            if size and duration:
                info = size / (duration / 60 * 0.0075) / 1000
        try:
            return info, int(float(info))
        except (ValueError, TypeError):
            return info, 0
