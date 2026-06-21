"""Command-line interface for chardet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chardet
from chardet._utils import DEFAULT_MAX_BYTES, ISO_TO_LANGUAGE
from chardet.enums import EncodingEra
from chardet.pipeline import DetectionDict

_ERA_NAMES = [e.name.lower() for e in EncodingEra if e.bit_count() == 1] + ["all"]


def _print_result(
    result: DetectionDict, label: str, *, minimal: bool, language: bool
) -> None:
    """Print a detection result to stdout."""
    if minimal:
        if language:
            iso = result["language"] or "und"
            print(f"{result['encoding']} {iso}")
        else:
            print(result["encoding"])
    elif language:
        iso = result["language"] or "und"
        name = ISO_TO_LANGUAGE.get(iso, iso).title()
        print(
            f"{label}: {result['encoding']} {iso} ({name}) "
            f"with confidence {result['confidence']}"
        )
    else:
        print(f"{label}: {result['encoding']} with confidence {result['confidence']}")


def main(argv: list[str] | None = None) -> None:
    """Run the ``chardetect`` command-line tool.

    :param argv: Command-line arguments.  Defaults to ``sys.argv[1:]``.
    """
    parser = argparse.ArgumentParser(description="Detect character encoding of files.")
    parser.add_argument("files", nargs="*", help="Files to detect encoding of")
    parser.add_argument(
        "--minimal", action="store_true", help="Output only the encoding name"
    )
    parser.add_argument(
        "-l",
        "--language",
        action="store_true",
        help="Include detected language in output",
    )
    parser.add_argument(
        "-e",
        "--encoding-era",
        default=None,
        choices=_ERA_NAMES,
        help="Encoding era filter",
    )
    parser.add_argument(
        "-i",
        "--include-encodings",
        default=None,
        help="Comma-separated list of encodings to consider",
    )
    parser.add_argument(
        "-x",
        "--exclude-encodings",
        default=None,
        help="Comma-separated list of encodings to exclude",
    )
    parser.add_argument(
        "--no-match-encoding",
        default="cp1252",
        help="Encoding to return when detection is inconclusive (default: cp1252)",
    )
    parser.add_argument(
        "--empty-input-encoding",
        default="utf-8",
        help="Encoding to return for empty input (default: utf-8)",
    )
    parser.add_argument(
        "--version", action="version", version=f"chardet {chardet.__version__}"
    )

    args = parser.parse_args(argv)

    era = (
        EncodingEra[args.encoding_era.upper()] if args.encoding_era else EncodingEra.ALL
    )

    include = (
        [s.strip() for s in args.include_encodings.split(",")]
        if args.include_encodings
        else None
    )
    exclude = (
        [s.strip() for s in args.exclude_encodings.split(",")]
        if args.exclude_encodings
        else None
    )

    if args.files:
        errors = 0
        for filepath in args.files:
            try:
                with Path(filepath).open("rb") as f:
                    data = f.read(DEFAULT_MAX_BYTES)
            except OSError as e:
                print(f"chardetect: {filepath}: {e}", file=sys.stderr)
                errors += 1
                continue
            try:
                result = chardet.detect(
                    data,
                    encoding_era=era,
                    include_encodings=include,
                    exclude_encodings=exclude,
                    no_match_encoding=args.no_match_encoding,
                    empty_input_encoding=args.empty_input_encoding,
                )
            except Exception as e:  # noqa: BLE001
                print(f"chardetect: {filepath}: detection failed: {e}", file=sys.stderr)
                errors += 1
                continue
            _print_result(
                result, filepath, minimal=args.minimal, language=args.language
            )
        if errors == len(args.files):
            sys.exit(1)
    else:
        data = sys.stdin.buffer.read(DEFAULT_MAX_BYTES)
        try:
            result = chardet.detect(
                data,
                encoding_era=era,
                include_encodings=include,
                exclude_encodings=exclude,
                no_match_encoding=args.no_match_encoding,
                empty_input_encoding=args.empty_input_encoding,
            )
        except Exception as e:  # noqa: BLE001
            print(f"chardetect: stdin: detection failed: {e}", file=sys.stderr)
            sys.exit(1)
        _print_result(result, "stdin", minimal=args.minimal, language=args.language)


if __name__ == "__main__":  # pragma: no cover
    main()
