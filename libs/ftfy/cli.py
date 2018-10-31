"""
A command-line utility for fixing text found in a file.
"""

import sys
import io
import codecs
from ftfy import fix_file, __version__
from ftfy.compatibility import PYTHON2


ENCODE_ERROR_TEXT_UNIX = """ftfy error:
Unfortunately, this output stream does not support Unicode.

Your system locale may be very old or misconfigured. You should use a locale
that supports UTF-8. One way to do this is to `export LANG=C.UTF-8`.
"""

ENCODE_ERROR_TEXT_WINDOWS = """ftfy error:
Unfortunately, this output stream does not support Unicode.

You might be trying to output to the Windows Command Prompt (cmd.exe), which
does not fully support Unicode for historical reasons. In general, we recommend
finding a way to run Python without using cmd.exe.

You can work around this problem by using the '-o filename' option in ftfy to
output to a file instead.
"""

DECODE_ERROR_TEXT = """ftfy error:
This input couldn't be decoded as %r. We got the following error:

    %s

ftfy works best when its input is in a known encoding. You can use `ftfy -g`
to guess, if you're desperate. Otherwise, give the encoding name with the
`-e` option, such as `ftfy -e latin-1`.
"""


def main():
    """
    Run ftfy as a command-line utility.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="ftfy (fixes text for you), version %s" % __version__
    )
    parser.add_argument('filename', default='-', nargs='?',
                        help='The file whose Unicode is to be fixed. Defaults '
                             'to -, meaning standard input.')
    parser.add_argument('-o', '--output', type=str, default='-',
                        help='The file to output to. Defaults to -, meaning '
                             'standard output.')
    parser.add_argument('-g', '--guess', action='store_true',
                        help="Ask ftfy to guess the encoding of your input. "
                             "This is risky. Overrides -e.")
    parser.add_argument('-e', '--encoding', type=str, default='utf-8',
                        help='The encoding of the input. Defaults to UTF-8.')
    parser.add_argument('-n', '--normalization', type=str, default='NFC',
                        help='The normalization of Unicode to apply. '
                             'Defaults to NFC. Can be "none".')
    parser.add_argument('--preserve-entities', action='store_true',
                        help="Leave HTML entities as they are. The default "
                             "is to decode them, as long as no HTML tags "
                             "have appeared in the file.")

    args = parser.parse_args()

    encoding = args.encoding
    if args.guess:
        encoding = None

    if args.filename == '-':
        # Get a standard input stream made of bytes, so we can decode it as
        # whatever encoding is necessary.
        if PYTHON2:
            file = sys.stdin
        else:
            file = sys.stdin.buffer
    else:
        file = open(args.filename, 'rb')

    if args.output == '-':
        encode_output = PYTHON2
        outfile = sys.stdout
    else:
        encode_output = False
        outfile = io.open(args.output, 'w', encoding='utf-8')

    normalization = args.normalization
    if normalization.lower() == 'none':
        normalization = None

    if args.preserve_entities:
        fix_entities = False
    else:
        fix_entities = 'auto'

    try:
        for line in fix_file(file, encoding=encoding,
                             fix_entities=fix_entities,
                             normalization=normalization):
            if encode_output:
                outfile.write(line.encode('utf-8'))
            else:
                try:
                    outfile.write(line)
                except UnicodeEncodeError:
                    if sys.platform == 'win32':
                        sys.stderr.write(ENCODE_ERROR_TEXT_WINDOWS)
                    else:
                        sys.stderr.write(ENCODE_ERROR_TEXT_UNIX)
                    sys.exit(1)
    except UnicodeDecodeError as err:
        sys.stderr.write(DECODE_ERROR_TEXT % (encoding, err))
        sys.exit(1)


if __name__ == '__main__':
    main()
