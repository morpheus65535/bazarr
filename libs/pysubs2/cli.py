from __future__ import unicode_literals, print_function
import argparse
import codecs
import os
import re
import os.path as op
import io
from io import open
import sys
from textwrap import dedent
from .formats import get_file_extension
from .time import make_time
from .ssafile import SSAFile
from .common import PY3, VERSION


def positive_float(s):
    x = float(s)
    if not x > 0:
        raise argparse.ArgumentTypeError("%r is not a positive number" % s)
    return x

def character_encoding(s):
    try:
        codecs.lookup(s)
        return s
    except LookupError:
        raise argparse.ArgumentError

def time(s):
    d = {}
    for v, k in re.findall(r"(\d*\.?\d*)(ms|m|s|h)", s):
        d[k] = float(v)
    return make_time(**d)


def change_ext(path, ext):
    base, _ = op.splitext(path)
    return base + ext


class Pysubs2CLI(object):
    def __init__(self):
        parser = self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                                       prog="pysubs2",
                                                       description=dedent("""
                                                       The pysubs2 CLI for processing subtitle files.
                                                       https://github.com/tkarabela/pysubs2
                                                       """),
                                                       epilog=dedent("""
                                                       usage examples:
                                                         python -m pysubs2 --to srt *.ass
                                                         python -m pysubs2 --to microdvd --fps 23.976 *.ass
                                                         python -m pysubs2 --shift 0.3s *.srt
                                                         python -m pysubs2 --shift 0.3s <my_file.srt >retimed_file.srt
                                                         python -m pysubs2 --shift-back 0.3s --output-dir retimed *.srt
                                                         python -m pysubs2 --transform-framerate 25 23.976 *.srt"""))

        parser.add_argument("files", nargs="*", metavar="FILE",
                            help="Input subtitle files. Can be in SubStation Alpha (*.ass, *.ssa), SubRip (*.srt) or "
                                 "MicroDVD (*.sub) formats. When no files are specified, pysubs2 will work as a pipe, "
                                 "reading from standard input and writing to standard output.")

        parser.add_argument("-v", "--version", action="version", version="pysubs2 %s" % VERSION)

        parser.add_argument("-f", "--from", choices=["ass", "ssa", "srt", "microdvd", "json"], dest="input_format",
                            help="By default, subtitle format is detected from the file. This option can be used to "
                                 "skip autodetection and force specific format. Generally, it should never be needed.")
        parser.add_argument("-t", "--to", choices=["ass", "ssa", "srt", "microdvd", "json"], dest="output_format",
                            help="Convert subtitle files to given format. By default, each file is saved in its "
                                 "original format.")
        parser.add_argument("--input-enc", metavar="ENCODING", default="iso-8859-1", type=character_encoding,
                            help="Character encoding for input files. By default, ISO-8859-1 is used for both "
                                 "input and output, which should generally work (for 8-bit encodings).")
        parser.add_argument("--output-enc", metavar="ENCODING", type=character_encoding,
                            help="Character encoding for output files. By default, it is the same as input encoding. "
                                 "If you wish to convert between encodings, make sure --input-enc is set correctly! "
                                 "Otherwise, your output files will probably be corrupted. It's a good idea to "
                                 "back up your files or use the -o option.")
        parser.add_argument("--fps", metavar="FPS", type=positive_float,
                            help="This argument specifies framerate for MicroDVD files. By default, framerate "
                                 "is detected from the file. Use this when framerate specification is missing "
                                 "or to force different framerate.")
        parser.add_argument("-o", "--output-dir", metavar="DIR",
                            help="Use this to save all files to given directory. By default, every file is saved to its parent directory, "
                                 "ie. unless it's being saved in different subtitle format (and thus with different file extension), "
                                 "it overwrites the original file.")

        group = parser.add_mutually_exclusive_group()

        group.add_argument("--shift", metavar="TIME", type=time,
                           help="Delay all subtitles by given time amount. Time is specified like this: '1m30s', '0.5s', ...")
        group.add_argument("--shift-back", metavar="TIME", type=time,
                           help="The opposite of --shift (subtitles will appear sooner).")
        group.add_argument("--transform-framerate", nargs=2, metavar=("FPS1", "FPS2"), type=positive_float,
                           help="Multiply all timestamps by FPS1/FPS2 ratio.")

    def __call__(self, argv):
        try:
            self.main(argv)
        except KeyboardInterrupt:
            exit("\nAborted by user.")

    def main(self, argv):
        args = self.parser.parse_args(argv)
        errors = 0

        if args.output_dir and not op.exists(args.output_dir):
            os.makedirs(args.output_dir)

        if args.output_enc is None:
            args.output_enc = args.input_enc

        if args.files:
            for path in args.files:
                if not op.exists(path):
                    print("Skipping", path, "(does not exist)")
                    errors += 1
                elif not op.isfile(path):
                    print("Skipping", path, "(not a file)")
                    errors += 1
                else:
                    with open(path, encoding=args.input_enc) as infile:
                        subs = SSAFile.from_file(infile, args.input_format, args.fps)

                    self.process(subs, args)

                    if args.output_format is None:
                        outpath = path
                        output_format = subs.format
                    else:
                        ext = get_file_extension(args.output_format)
                        outpath = change_ext(path, ext)
                        output_format = args.output_format

                    if args.output_dir is not None:
                        _, filename = op.split(outpath)
                        outpath = op.join(args.output_dir, filename)

                    with open(outpath, "w", encoding=args.output_enc) as outfile:
                        subs.to_file(outfile, output_format, args.fps)
        else:
            if PY3:
                infile = io.TextIOWrapper(sys.stdin.buffer, args.input_enc)
                outfile = io.TextIOWrapper(sys.stdout.buffer, args.output_enc)
            else:
                infile = io.TextIOWrapper(sys.stdin, args.input_enc)
                outfile = io.TextIOWrapper(sys.stdout, args.output_enc)

            subs = SSAFile.from_file(infile, args.input_format, args.fps)
            self.process(subs, args)
            output_format = args.output_format or subs.format
            subs.to_file(outfile, output_format, args.fps)

        return (0 if errors == 0 else 1)

    @staticmethod
    def process(subs, args):
        if args.shift is not None:
            subs.shift(ms=args.shift)
        elif args.shift_back is not None:
            subs.shift(ms=-args.shift_back)
        elif args.transform_framerate is not None:
            in_fps, out_fps = args.transform_framerate
            subs.transform_framerate(in_fps, out_fps)


def __main__():
    cli = Pysubs2CLI()
    rv = cli(sys.argv[1:])
    sys.exit(rv)


if __name__ == "__main__":
    __main__()
