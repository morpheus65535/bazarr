"""Guess the natural language of a text
"""

import argparse
import locale
import os
import sys

import guess_language.console_mode #@UnusedImport


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
        prog="{} -m {}".format(os.path.basename(sys.executable),
                               "guess_language")
    )
    parser.add_argument("file",
                        help="plain text file or “-” for stdin")
    parser.add_argument("-c", "--encoding",
                        help="input encoding")
    parser.add_argument("--disable-enchant", dest="use_enchant",
                        action="store_false",
                        help="disable enchant")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.file == "-":
        file = sys.stdin.fileno()
        encoding = args.encoding or (
            sys.stdin.encoding if sys.stdin.isatty()
            else locale.getpreferredencoding()
        )
    else:
        file = args.file
        encoding = args.encoding or "utf-8"

    with open(file, encoding=encoding) as f:
        text = "".join(f.readlines())

    if not args.use_enchant:
        guess_language.use_enchant(False)
    tag = guess_language.guess_language(text)
    print(tag)

    return 0 if tag else 1


if __name__ == "__main__":
    sys.exit(main())
