import argparse
import codecs
import os
import re
import os.path as op
from io import TextIOWrapper
import sys
from textwrap import dedent
from typing import List

from .formats import get_file_extension, FORMAT_IDENTIFIERS
from .time import make_time
from .ssafile import SSAFile
from .common import VERSION
import logging


def positive_float(s: str) -> float:
    x = float(s)
    if not x > 0:
        raise argparse.ArgumentTypeError(f"{s!r} is not a positive number")
    return x


def character_encoding(s: str) -> str:
    try:
        codecs.lookup(s)
        return s
    except LookupError:
        raise argparse.ArgumentError(None, f"unknown character encoding: {s}")


def time(s: str) -> int:
    d = {}
    for v, k in re.findall(r"(\d*\.?\d*)(ms|m|s|h)", s):
        d[k] = float(v)
    return make_time(**d)  # type: ignore  # Argument 1 has incomp. type "**Dict[Any, float]"; expected "Optional[int]"


def change_ext(path: str, ext: str) -> str:
    base, _ = op.splitext(path)
    return base + ext


class Pysubs2CLI:
    def __init__(self) -> None:
        parser = self.parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                                       prog="pysubs2",
                                                       description=dedent("""
                                                       The pysubs2 CLI for processing subtitle files.
                                                       https://github.com/tkarabela/pysubs2
                                                       """),
                                                       epilog=dedent("""
                                                       usage examples:
                                                         python -m pysubs2 --to srt *.ass
                                                         python -m pysubs2 --to srt --clean *.ass
                                                         python -m pysubs2 --to microdvd --fps 23.976 *.ass
                                                         python -m pysubs2 --shift 0.3s *.srt
                                                         python -m pysubs2 --shift 0.3s <my_file.srt >retimed_file.srt
                                                         python -m pysubs2 --shift-back 0.3s --output-dir retimed *.srt
                                                         python -m pysubs2 --transform-framerate 25 23.976 *.srt"""))

        parser.add_argument("files", nargs="*", metavar="FILE",
                            help="Input subtitle files. Can be in SubStation Alpha (*.ass, *.ssa), SubRip (*.srt), "
                                 "MicroDVD (*.sub) or other supported format. When no files are specified, "
                                 "pysubs2 will work as a pipe, reading from standard input and writing to standard output.")

        parser.add_argument("-v", "--version", action="version", version=f"pysubs2 {VERSION}")

        parser.add_argument("-f", "--from", choices=FORMAT_IDENTIFIERS, dest="input_format",
                            help="By default, subtitle format is detected from the file. This option can be used to "
                                 "skip autodetection and force specific format. Generally, it should never be needed.")
        parser.add_argument("-t", "--to", choices=FORMAT_IDENTIFIERS, dest="output_format",
                            help="Convert subtitle files to given format. By default, each file is saved in its "
                                 "original format.")
        parser.add_argument("--input-enc", metavar="ENCODING", default="utf-8", type=character_encoding,
                            help="Character encoding for input files. By default, UTF-8 is used for both "
                                 "input and output.")
        parser.add_argument("--output-enc", metavar="ENCODING", type=character_encoding,
                            help="Character encoding for output files. By default, it is the same as input encoding. "
                                 "If you wish to convert between encodings, make sure --input-enc is set correctly! "
                                 "Otherwise, your output files will probably be corrupted. It's a good idea to "
                                 "back up your files or use the -o option.")
        parser.add_argument("--enc-error-handling", choices=("strict", "surrogateescape"),
                            default="surrogateescape",
                            help="Character encoding error handling for input and output. Defaults to 'surrogateescape' "
                                 "which passes through unrecognized characters to output unchanged. Use 'strict' if "
                                 "you want the command to fail when encountering a character incompatible with selected "
                                 "input/output encoding.")
        parser.add_argument("--fps", metavar="FPS", type=positive_float,
                            help="This argument specifies framerate for MicroDVD files. By default, framerate "
                                 "is detected from the file. Use this when framerate specification is missing "
                                 "or to force different framerate.")
        parser.add_argument("-o", "--output-dir", metavar="DIR",
                            help="Use this to save all files to given directory. By default, every file is saved to its parent directory, "
                                 "ie. unless it's being saved in different subtitle format (and thus with different file extension), "
                                 "it overwrites the original file.")
        parser.add_argument("--clean", action="store_true",
                            help="Attempt to remove non-essential subtitles (eg. karaoke, SSA drawing tags), "
                                 "strip styling information when saving to non-SSA formats")
        parser.add_argument("--verbose", action="store_true",
                            help="Print misc logging")

        group = parser.add_mutually_exclusive_group()

        group.add_argument("--shift", metavar="TIME", type=time,
                           help="Delay all subtitles by given time amount. Time is specified like this: '1m30s', '0.5s', ...")
        group.add_argument("--shift-back", metavar="TIME", type=time,
                           help="The opposite of --shift (subtitles will appear sooner).")
        group.add_argument("--transform-framerate", nargs=2, metavar=("FPS1", "FPS2"), type=positive_float,
                           help="Multiply all timestamps by FPS1/FPS2 ratio.")

        extra_srt_options = parser.add_argument_group("optional arguments (SRT)")
        extra_srt_options.add_argument("--srt-keep-unknown-html-tags", action="store_true",
                                       help="(input) do not strip unrecognized HTML tags")
        extra_srt_options.add_argument("--srt-keep-html-tags", action="store_true",
                                       help="(input) do not convert HTML tags to SubStation internally,"
                                            " this implies --srt-keep-unknown-html-tags")
        extra_srt_options.add_argument("--srt-keep-ssa-tags", action="store_true",
                                       help="(output) do not convert/strip SubStation tags for output")

        extra_sub_options = parser.add_argument_group("optional arguments (MicroDVD)")
        extra_sub_options.add_argument("--sub-no-write-fps-declaration", action="store_true",
                                       help="(output) omit writing FPS as first zero-length subtitle")

    def __call__(self, argv: List[str]) -> int:
        try:
            return self.main(argv)
        except KeyboardInterrupt:
            print("\nAborted by user.", file=sys.stderr)
            return 1

    def main(self, argv: List[str]) -> int:
        args = self.parser.parse_args(argv)
        errors = 0

        if args.verbose:
            logging.basicConfig(level=logging.DEBUG)

        if args.output_dir and not op.exists(args.output_dir):
            os.makedirs(args.output_dir)

        if args.output_enc is None:
            args.output_enc = args.input_enc

        extra_input_args = {}
        extra_output_args = {}
        if args.srt_keep_unknown_html_tags:
            extra_input_args["keep_unknown_html_tags"] = True
        if args.srt_keep_html_tags:
            extra_input_args["keep_html_tags"] = True
        if args.srt_keep_ssa_tags:
            extra_output_args["keep_ssa_tags"] = True
        if args.sub_no_write_fps_declaration:
            extra_output_args["write_fps_declaration"] = False
        logging.debug("Extra arguments to SSAFile.from_file(): %r", extra_input_args)
        logging.debug("Extra arguments to SSAFile.to_file(): %r", extra_output_args)

        if args.files:
            for path in args.files:
                if not op.exists(path):
                    print("Skipping", path, "(does not exist)")
                    errors += 1
                elif not op.isfile(path):
                    print("Skipping", path, "(not a file)")
                    errors += 1
                else:
                    with open(path, encoding=args.input_enc, errors=args.enc_error_handling) as infile:
                        subs = SSAFile.from_file(infile, args.input_format, args.fps, **extra_input_args)

                    self.process(subs, args)

                    if args.output_format is None:
                        outpath = path
                        output_format = subs.format
                        assert output_format is not None, "subs.format must not be None (it was read from file)"
                    else:
                        ext = get_file_extension(args.output_format)
                        outpath = change_ext(path, ext)
                        output_format = args.output_format
                        assert output_format is not None, "args.output_format must not be None (see if/else)"

                    if args.output_dir is not None:
                        _, filename = op.split(outpath)
                        outpath = op.join(args.output_dir, filename)

                    with open(outpath, "w", encoding=args.output_enc, errors=args.enc_error_handling) as outfile:
                        subs.to_file(outfile, output_format, args.fps, apply_styles=not args.clean,
                                     **extra_output_args)
        elif not sys.stdin.isatty():
            infile = TextIOWrapper(sys.stdin.buffer, encoding=args.input_enc, errors=args.enc_error_handling)
            outfile = TextIOWrapper(sys.stdout.buffer, encoding=args.output_enc, errors=args.enc_error_handling)

            subs = SSAFile.from_file(infile, args.input_format, args.fps)
            self.process(subs, args)
            output_format = args.output_format or subs.format
            assert output_format is not None, "output_format must not be None (it's either given or inferred at read time)"
            subs.to_file(outfile, output_format, args.fps, apply_styles=not args.clean)
        else:
            self.parser.print_help()
            errors += 1

        return 0 if errors == 0 else 1

    @staticmethod
    def process(subs: SSAFile, args: argparse.Namespace) -> None:
        if args.shift is not None:
            subs.shift(ms=args.shift)
        elif args.shift_back is not None:
            subs.shift(ms=-args.shift_back)
        elif args.transform_framerate is not None:
            in_fps, out_fps = args.transform_framerate
            subs.transform_framerate(in_fps, out_fps)

        if args.clean:
            subs.remove_miscellaneous_events()


def __main__() -> None:
    cli = Pysubs2CLI()
    rv = cli(sys.argv[1:])
    sys.exit(rv)


if __name__ == "__main__":
    __main__()
