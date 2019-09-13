# -*- coding: utf-8 -*-
import re
from datetime import time

from subliminal.subtitles import Cue

index_re = re.compile(r'(?P<index>\d+)')
timing_re = re.compile(r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}),(?P<milliseconds>\d{3})')


class SubripReadError(Exception):
    pass


class SubripReadIndexError(SubripReadError):
    pass


class SubripReader(object):
    INDEX = 1
    TIMINGS = 2
    TEXT = 3

    def __init__(self):
        self.state = self.INDEX

    def read(self, content):
        pass

    def read_line(self, line):
        if self.state == self.INDEX:
            if index_re.match(line):
                raise SubripReadIndexError


def read_cue(stream):
    """Attempt to parse a complete Cue from the stream"""
    # skip blank lines
    line = ''
    while not line:
        line = stream.readline()

    # parse index
    if not index_re.match(line):
        raise SubripReadIndexError

    # parse timings
    line = stream.readline()
    if '-->' not in line:
        raise SubripReadError
    timings = line.split('-->')
    if not len(timings):
        raise SubripReadError

    # parse start time
    match = timing_re.match(timings[0].strip())
    if not match:
        raise SubripReadError
    start_time = time(**match.groupdict())

    # parse end time
    match = timing_re.match(timings[0].strip())
    if not match:
        raise SubripReadError
    end_time = time(**match.groupdict())




class SubripSubtitle(object):
    def __init__(self):
        self.cues = []


if __name__ == '__main__':
    print read_cue('toto')
      i = 0
    for x in read_cue('toto'):
        print x
        if i > 10:
            break
        i += 1
