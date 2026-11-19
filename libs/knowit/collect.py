"""Collect the provider output of a whole media library, for offline analysis.

A collect record is the per-file part of a bug report, written one line at a time so a
library of thousands of files never has to fit in memory.
"""

import datetime
import gzip
import hashlib
import io
import json
import os
import time
import traceback
import typing

from knowit import __version__, api
from knowit.bugreport import describe_path, mask_home, mask_path, probe_provider
from knowit.environment import collect_environment
from knowit.provider import run_command
from knowit.serializer import get_json_encoder

#: Bumped whenever the record layout changes in a way readers must know about.
COLLECT_VERSION = 1

#: A new part starts above this size, so each part can be attached to a GitHub issue (25 MB).
PART_SIZE = 20 * 1024 * 1024

#: Where the capture goes when the user gives no output. It never holds a media name.
DEFAULT_OUTPUT = 'knowit-collect.jsonl.gz'

#: Video frames that --deep reads. HDR10+ and the Dolby Vision RPU are only in the frames.
DEEP_FRAMES = 3

#: Frame keys that --deep keeps. The side data is the purpose, the rest locates it.
DEEP_FRAME_KEYS = ('key_frame', 'pict_type', 'side_data_list')

#: Keys that hold binary data. Masking keeps the length, so they are removed instead.
BLOB_KEYS = frozenset({'cover_data'})


def file_key(video_path: str) -> str:
    """Return a key for a file that does not disclose its path."""
    # fsencode keeps undecodable names intact, so two such files never share a key.
    return hashlib.sha256(os.fsencode(video_path)).hexdigest()


def strip_blobs(data: typing.Any) -> typing.Any:
    """Return a copy of `data` without the binary blobs."""
    if isinstance(data, dict):
        return {k: strip_blobs(v) for k, v in data.items() if str(k).lower() not in BLOB_KEYS}
    if isinstance(data, list):
        return [strip_blobs(item) for item in data]
    return data


def selected_providers(context: typing.Mapping[str, typing.Any]) -> list[str]:
    """Return the providers to probe: the one the user asked for, or all of them."""
    provider = context.get('provider')
    return [provider] if provider else list(api.provider_names)


def probe_frames(location: str, video_path: str) -> dict[str, typing.Any]:
    """Return the side data of the first video frames, with ffprobe."""
    start = time.perf_counter()
    output = run_command(
        [
            location,
            '-v',
            'error',
            '-select_streams',
            'v:0',
            '-read_intervals',
            f'%+#{DEEP_FRAMES}',
            '-show_frames',
            '-print_format',
            'json',
            video_path,
        ]
    )
    frames = (json.loads(output).get('frames') or []) if output else []
    return {
        'frames': [{k: frame[k] for k in DEEP_FRAME_KEYS if k in frame} for frame in frames],
        'seconds': round(time.perf_counter() - start, 3),
    }


def _deep_probe(video_path: str) -> dict[str, typing.Any]:
    """Run the deep probe, and keep the error instead of losing the whole file."""
    provider = api.available_providers.get('ffmpeg')
    location = getattr(provider.executor, 'location', None) if provider else None
    if not location:
        return {'error': 'ffprobe is not installed'}
    try:
        return probe_frames(location, video_path)
    except Exception as error:
        return {'error': f'{type(error).__name__}: {error}'}


def build_record(
    video_path: str | os.PathLike[str],
    context: typing.MutableMapping[str, typing.Any],
    anonymize: bool = True,
    deep: bool = False,
) -> dict[str, typing.Any]:
    """Build the record of one file, probing every selected provider."""
    text = os.fspath(video_path)
    record: dict[str, typing.Any] = {'key': file_key(text)}
    try:
        stat = os.stat(text)
        record['size'] = stat.st_size
        record['mtime'] = stat.st_mtime_ns
    except OSError:
        pass
    record['path'] = describe_path(text, anonymize)

    # Unknown values are reported against the path, see Reportable.report.
    context['path'] = text
    api.initialize(context)
    providers = {}
    for name in selected_providers(context):
        start = time.perf_counter()
        try:
            result = probe_provider(name, text, context, anonymize)
        except Exception:
            result = {'status': 'error', 'traceback': traceback.format_exc()}
        result['seconds'] = round(time.perf_counter() - start, 3)
        if 'raw' in result:
            result['raw'] = strip_blobs(result['raw'])
        if deep and name == 'ffmpeg' and result.get('status') == 'ok':
            result['deep'] = _deep_probe(text)
        providers[name] = result
    record['providers'] = mask_home(mask_path(providers, text)) if anonymize else providers

    return record


def build_header(
    context: typing.Mapping[str, typing.Any],
    anonymize: bool = True,
    deep: bool = False,
) -> dict[str, typing.Any]:
    """Build the first line of each part: what produced the records that follow."""
    header: dict[str, typing.Any] = {
        'knowit_collect': COLLECT_VERSION,
        'knowit_version': __version__,
        'generated_at': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'anonymized': anonymize,
        'deep': deep,
        'providers': selected_providers(context),
        'dependencies': dict(api.dependencies(context)),
    }
    try:
        header['environment'] = collect_environment(context)
    except Exception:
        header['environment'] = {'error': traceback.format_exc()}
    return mask_home(header) if anonymize else header


def part_path(output: str, number: int) -> str:
    """Return the file name of a part: `name.jsonl.gz`, then `name.part2.jsonl.gz`, and so on."""
    if number == 1:
        return output
    stem, gz = (output[:-3], '.gz') if output.endswith('.gz') else (output, '')
    stem, extension = os.path.splitext(stem)
    return f'{stem}.part{number}{extension}{gz}'


def existing_parts(output: str) -> list[str]:
    """Return the parts of an output that already exist, in order."""
    parts: list[str] = []
    while os.path.exists(path := part_path(output, len(parts) + 1)):
        parts.append(path)
    return parts


class Writer:
    """Append records to json lines parts, starting a new part above a size limit.

    A run never appends to an existing part: a gzip member cut by a crash would hide
    everything written after it.
    """

    def __init__(self, output: str, header: typing.Mapping[str, typing.Any], part_size: int = PART_SIZE):
        """Open the first free part."""
        self.output = output
        self.header = header
        self.part_size = part_size
        self.encoder = get_json_encoder({'profile': 'code'})
        self.number = len(existing_parts(output))
        self.written = 0
        self._file: io.BufferedIOBase | None = None
        self._stream: io.BufferedIOBase | None = None
        self._open_next_part()

    def _open_next_part(self) -> None:
        self.close()
        self.number += 1
        # The part stays open across write() calls. close() closes it.
        self._file = open(part_path(self.output, self.number), 'xb')  # noqa: SIM115
        self._stream = gzip.GzipFile(fileobj=self._file, mode='wb') if self.output.endswith('.gz') else self._file
        self._write_line(self.header)

    def _write_line(self, data: typing.Mapping[str, typing.Any]) -> None:
        assert self._file is not None and self._stream is not None
        line = json.dumps(data, cls=self.encoder, ensure_ascii=False) + '\n'
        # Lone surrogates from undecodable names cannot be encoded as utf-8 otherwise.
        self._stream.write(line.encode('utf-8', errors='backslashreplace'))
        self._stream.flush()

    def write(self, record: typing.Mapping[str, typing.Any]) -> None:
        """Append one record, and flush it so a stop loses at most this line."""
        assert self._file is not None
        if self.written and self._file.tell() >= self.part_size:
            self._open_next_part()
            self.written = 0
        self._write_line(record)
        self.written += 1

    def close(self) -> None:
        """Close the current part."""
        if self._stream is not None and self._stream is not self._file:
            self._stream.close()
        if self._file is not None:
            self._file.close()
        self._file = self._stream = None

    def __enter__(self) -> 'Writer':
        """Use the writer as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the writer."""
        self.close()


def read_part(path: str) -> typing.Iterator[dict[str, typing.Any]]:
    """Yield every header and record of one part. A damaged line or gzip end is skipped."""
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rb') as stream:
        try:
            for line in io.TextIOWrapper(stream, encoding='utf-8', errors='replace'):
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
        except (EOFError, OSError):
            return


def read_lines(output: str) -> typing.Iterator[dict[str, typing.Any]]:
    """Yield every header and record of all parts of an output."""
    for path in existing_parts(output):
        yield from read_part(path)


def read_done(output: str) -> dict[str, tuple[int | None, int | None]]:
    """Return the size and the mtime of each file already in the output, by key."""
    return {
        line['key']: (line.get('size'), line.get('mtime'))
        for line in read_lines(output)
        if isinstance(line, dict) and 'key' in line
    }


def is_done(
    video_path: str,
    done: typing.Mapping[str, tuple[int | None, int | None]],
) -> bool:
    """Return True when the file is in the output and did not change since."""
    try:
        stat = os.stat(video_path)
    except OSError:
        return False
    return done.get(file_key(video_path)) == (stat.st_size, stat.st_mtime_ns)


def run(
    video_paths: typing.Sequence[str],
    output: str,
    context: typing.MutableMapping[str, typing.Any],
    anonymize: bool = True,
    deep: bool = False,
    on_file: typing.Callable[[int, str, str], None] | None = None,
) -> dict[str, typing.Any]:
    """Capture every file that is not already in the output, and return a summary.

    A stop with Ctrl+C keeps what was written. The next run continues from there.
    """
    context['report'] = {}
    done = read_done(output)
    summary: dict[str, typing.Any] = {'files': len(video_paths), 'captured': 0, 'skipped': 0, 'errors': {}}
    writer: Writer | None = None
    try:
        for index, video_path in enumerate(video_paths, start=1):
            if is_done(video_path, done):
                summary['skipped'] += 1
                status = 'skipped'
            else:
                record = build_record(video_path, context, anonymize, deep)
                if writer is None:
                    writer = Writer(output, build_header(context, anonymize, deep))
                writer.write(record)
                summary['captured'] += 1
                failed = [n for n, r in record['providers'].items() if r.get('status') == 'error']
                for name in failed:
                    summary['errors'][name] = summary['errors'].get(name, 0) + 1
                status = f'errors: {", ".join(failed)}' if failed else 'captured'
            if on_file:
                on_file(index, video_path, status)
    except KeyboardInterrupt:
        summary['interrupted'] = True
    finally:
        if writer is not None:
            writer.close()

    summary['unknown'] = context['report']
    return summary
