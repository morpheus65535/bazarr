"""Console script for deep_translator."""

import argparse
import sys
from .google_trans import GoogleTranslator
from .mymemory import MyMemoryTranslator
from .pons import PonsTranslator
from .linguee import LingueeTranslator


def translate(args):
    """
    function used to provide translations from the parsed terminal arguments
    @param args: parsed terminal arguments
    @return: None
    """
    translator = None
    if args.translator == 'google':
        translator = GoogleTranslator(source=args.source, target=args.target)
    elif args.translator == 'pons':
        translator = PonsTranslator(source=args.source, target=args.target)
    elif args.translator == 'linguee':
        translator = LingueeTranslator(source=args.source, target=args.target)
    elif args.translator == 'mymemory':
        translator = MyMemoryTranslator(source=args.source, target=args.target)
    else:
        print("given translator is not supported. Please use a supported translator from the deep_translator tool")

    res = translator.translate(args.text)
    print(" | Translation from {} to {} |".format(args.source, args.target))
    print("Translated text: \n {}".format(res))


def main():
    """
    function responsible for parsing terminal arguments and provide them for further use in the translation process

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--translator', '-trans',
                        default='google', type=str, help="name of the translator you want to use")
    parser.add_argument('--source', '-src', type=str, help="source language to translate from", required=True)
    parser.add_argument('--target', '-tg', type=str, help="target language to translate to", required=True)
    parser.add_argument('--text', '-txt', type=str, help="text you want to translate", required=True)

    args = parser.parse_args()
    translate(args)
    # sys.exit()


if __name__ == "__main__":
    main()
