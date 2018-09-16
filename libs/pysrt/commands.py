#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable-all

import os
import re
import sys
import codecs
import shutil
import argparse
from textwrap import dedent

from chardet import detect
from pysrt import SubRipFile, SubRipTime, VERSION_STRING


def underline(string):
    return "\033[4m%s\033[0m" % string


class TimeAwareArgumentParser(argparse.ArgumentParser):

    RE_TIME_REPRESENTATION = re.compile(r'^\-?(\d+[hms]{0,2}){1,4}$')

    def parse_args(self, args=None, namespace=None):
        time_index = -1
        for index, arg in enumerate(args):
            match = self.RE_TIME_REPRESENTATION.match(arg)
            if match:
                time_index = index
                break

        if time_index >= 0:
            args.insert(time_index, '--')

        return super(TimeAwareArgumentParser, self).parse_args(args, namespace)


class SubRipShifter(object):

    BACKUP_EXTENSION = '.bak'
    RE_TIME_STRING = re.compile(r'(\d+)([hms]{0,2})')
    UNIT_RATIOS = {
        'ms': 1,
        '': SubRipTime.SECONDS_RATIO,
        's': SubRipTime.SECONDS_RATIO,
        'm': SubRipTime.MINUTES_RATIO,
        'h': SubRipTime.HOURS_RATIO,
    }
    DESCRIPTION = dedent("""\
        Srt subtitle editor

        It can either shift, split or change the frame rate.
    """)
    TIMESTAMP_HELP = "A timestamp in the form: [-][Hh][Mm]S[s][MSms]"
    SHIFT_EPILOG = dedent("""\

        Examples:
            1 minute and 12 seconds foreward (in place):
                $ srt -i shift 1m12s movie.srt

            half a second foreward:
                $ srt shift 500ms movie.srt > othername.srt

            1 second and half backward:
                $ srt -i shift -1s500ms movie.srt

            3 seconds backward:
                $ srt -i shift -3 movie.srt
    """)
    RATE_EPILOG = dedent("""\

        Examples:
            Convert 23.9fps subtitles to 25fps:
                $ srt -i rate 23.9 25 movie.srt
    """)
    LIMITS_HELP = "Each parts duration in the form: [Hh][Mm]S[s][MSms]"
    SPLIT_EPILOG = dedent("""\

        Examples:
            For a movie in 2 parts with the first part 48 minutes and 18 seconds long:
                $ srt split 48m18s movie.srt
                => creates movie.1.srt and movie.2.srt

            For a movie in 3 parts of 20 minutes each:
                $ srt split 20m 20m movie.srt
                => creates movie.1.srt, movie.2.srt and movie.3.srt
    """)
    FRAME_RATE_HELP = "A frame rate in fps (commonly 23.9 or 25)"
    ENCODING_HELP = dedent("""\
        Change file encoding. Useful for players accepting only latin1 subtitles.
        List of supported encodings: http://docs.python.org/library/codecs.html#standard-encodings
    """)
    BREAK_EPILOG = dedent("""\
        Break lines longer than defined length
    """)
    LENGTH_HELP = "Maximum number of characters per line"

    def __init__(self):
        self.output_file_path = None

    def build_parser(self):
        parser = TimeAwareArgumentParser(description=self.DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-i', '--in-place', action='store_true', dest='in_place',
            help="Edit file in-place, saving a backup as file.bak (do not works for the split command)")
        parser.add_argument('-e', '--output-encoding', metavar=underline('encoding'), action='store', dest='output_encoding',
            type=self.parse_encoding, help=self.ENCODING_HELP)
        parser.add_argument('-v', '--version', action='version', version='%%(prog)s %s' % VERSION_STRING)
        subparsers = parser.add_subparsers(title='commands')

        shift_parser = subparsers.add_parser('shift', help="Shift subtitles by specified time offset", epilog=self.SHIFT_EPILOG, formatter_class=argparse.RawTextHelpFormatter)
        shift_parser.add_argument('time_offset', action='store', metavar=underline('offset'),
            type=self.parse_time, help=self.TIMESTAMP_HELP)
        shift_parser.set_defaults(action=self.shift)

        rate_parser = subparsers.add_parser('rate', help="Convert subtitles from a frame rate to another", epilog=self.RATE_EPILOG, formatter_class=argparse.RawTextHelpFormatter)
        rate_parser.add_argument('initial', action='store', type=float, help=self.FRAME_RATE_HELP)
        rate_parser.add_argument('final', action='store', type=float, help=self.FRAME_RATE_HELP)
        rate_parser.set_defaults(action=self.rate)

        split_parser = subparsers.add_parser('split', help="Split a file in multiple parts", epilog=self.SPLIT_EPILOG, formatter_class=argparse.RawTextHelpFormatter)
        split_parser.add_argument('limits', action='store', nargs='+', type=self.parse_time, help=self.LIMITS_HELP)
        split_parser.set_defaults(action=self.split)

        break_parser = subparsers.add_parser('break', help="Break long lines", epilog=self.BREAK_EPILOG, formatter_class=argparse.RawTextHelpFormatter)
        break_parser.add_argument('length', action='store', type=int, help=self.LENGTH_HELP)
        break_parser.set_defaults(action=self.break_lines)

        parser.add_argument('file', action='store')

        return parser

    def run(self, args):
        self.arguments = self.build_parser().parse_args(args)
        if self.arguments.in_place:
            self.create_backup()
        self.arguments.action()

    def parse_time(self, time_string):
        negative = time_string.startswith('-')
        if negative:
            time_string = time_string[1:]
        ordinal = sum(int(value) * self.UNIT_RATIOS[unit] for value, unit
                        in self.RE_TIME_STRING.findall(time_string))
        return -ordinal if negative else ordinal

    def parse_encoding(self, encoding_name):
        try:
            codecs.lookup(encoding_name)
        except LookupError as error:
            raise argparse.ArgumentTypeError(error.message)
        return encoding_name

    def shift(self):
        self.input_file.shift(milliseconds=self.arguments.time_offset)
        self.input_file.write_into(self.output_file)

    def rate(self):
        ratio = self.arguments.final / self.arguments.initial
        self.input_file.shift(ratio=ratio)
        self.input_file.write_into(self.output_file)

    def split(self):
        limits = [0] + self.arguments.limits + [self.input_file[-1].end.ordinal + 1]
        base_name, extension = os.path.splitext(self.arguments.file)
        for index, (start, end) in enumerate(zip(limits[:-1], limits[1:])):
            file_name = '%s.%s%s' % (base_name, index + 1, extension)
            part_file = self.input_file.slice(ends_after=start, starts_before=end)
            part_file.shift(milliseconds=-start)
            part_file.clean_indexes()
            part_file.save(path=file_name, encoding=self.output_encoding)

    def create_backup(self):
        backup_file = self.arguments.file + self.BACKUP_EXTENSION
        if not os.path.exists(backup_file):
            shutil.copy2(self.arguments.file, backup_file)
        self.output_file_path = self.arguments.file
        self.arguments.file = backup_file

    def break_lines(self):
        split_re = re.compile(r'(.{,%i})(?:\s+|$)' % self.arguments.length)
        for item in self.input_file:
            item.text = '\n'.join(split_re.split(item.text)[1::2])
        self.input_file.write_into(self.output_file)

    @property
    def output_encoding(self):
        return self.arguments.output_encoding or self.input_file.encoding

    @property
    def input_file(self):
        if not hasattr(self, '_source_file'):
            with open(self.arguments.file, 'rb') as f:
                content = f.read()
                encoding = detect(content).get('encoding')
                encoding = self.normalize_encoding(encoding)

            self._source_file = SubRipFile.open(self.arguments.file,
                encoding=encoding, error_handling=SubRipFile.ERROR_LOG)
        return self._source_file

    @property
    def output_file(self):
        if not hasattr(self, '_output_file'):
            if self.output_file_path:
                self._output_file = codecs.open(self.output_file_path, 'w+', encoding=self.output_encoding)
            else:
                self._output_file = sys.stdout
        return self._output_file

    def normalize_encoding(self, encoding):
        return encoding.lower().replace('-', '_')


def main():
    SubRipShifter().run(sys.argv[1:])

if __name__ == '__main__':
    main()
