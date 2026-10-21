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
    result: DetectionDict, label: str, *, minimal: bool, language: bool, mime_type: bool
) -> None:
    """Print a detection result to stdout."""
    desc = str(result["encoding"])
    if minimal:
        if language:
            desc += f" {result['language'] or 'und'}"
        if mime_type:
            desc += f" {result['mime_type'] or 'application/octet-stream'}"
        print(desc)
    else:
        if language:
            iso = result["language"] or "und"
            name = ISO_TO_LANGUAGE.get(iso, iso).title()
            desc += f" {iso} ({name})"
        if mime_type:
            desc += f" {result['mime_type'] or 'application/octet-stream'}"
        print(f"{label}: {desc} with confidence {result['confidence']}")


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
        "-m",
        "--mime-type",
        action="store_true",
        help="Include detected MIME type in output",
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
                    # One byte past the cap lets detect() tell truncated
                    # input from input that ends exactly at the cap.  It
                    # does its own slicing to max_bytes.
                    data = f.read(DEFAULT_MAX_BYTES + 1)
            except OSError as e:
                print(f"chardetect: {filepath}: {e}", file=sys.stderr)
                errors += 1
                continue
            try:
                result = chardet.detect(
                    data,
                    encoding_era=era,
                    max_bytes=DEFAULT_MAX_BYTES,
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
                result,
                filepath,
                minimal=args.minimal,
                language=args.language,
                mime_type=args.mime_type,
            )
        if errors == len(args.files):
            sys.exit(1)
    else:
        # Same reason as the file read above: one extra byte so detect()
        # can see that the input was truncated.
        data = sys.stdin.buffer.read(DEFAULT_MAX_BYTES + 1)
        try:
            result = chardet.detect(
                data,
                encoding_era=era,
                max_bytes=DEFAULT_MAX_BYTES,
                include_encodings=include,
                exclude_encodings=exclude,
                no_match_encoding=args.no_match_encoding,
                empty_input_encoding=args.empty_input_encoding,
            )
        except Exception as e:  # noqa: BLE001
            print(f"chardetect: stdin: detection failed: {e}", file=sys.stderr)
            sys.exit(1)
        _print_result(
            result,
            "stdin",
            minimal=args.minimal,
            language=args.language,
            mime_type=args.mime_type,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
