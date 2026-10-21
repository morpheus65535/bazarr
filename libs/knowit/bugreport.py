"""Build a self-contained bug report that can be attached to an issue.

Reproducing a knowit bug almost never needs the media file itself: it needs the raw
output the backend produced for it. That output is a few kilobytes of text, it carries
no copyrighted content, and it is exactly what `tests/data/<provider>` is made of.
"""

import datetime
import json
import os
import sys
import traceback
import typing
import unicodedata

import yaml

from knowit import __version__, api
from knowit.environment import collect_environment
from knowit.serializer import get_yaml_dumper

#: Bumped whenever the report layout changes in a way readers must know about.
REPORT_VERSION = 1

#: Free text in raw backend output. Values are masked, never dropped.
RAW_TEXT_KEYS = frozenset(
    {
        '@ref',
        'album',
        'album_performer',
        'artist',
        'author',
        'comment',
        'comment_ext',
        'completename',
        'completename_last',
        'composer',
        'contenttype',
        'copyright',
        'cover_data',
        'date_local',
        'date_utc',
        'description',
        'director',
        'encoded_by',
        'encoded_date',
        'encoded_library',
        'encoded_library_string',
        'encoded_library_version',
        'episode_id',
        'file_created_date',
        'file_created_date_local',
        'file_modified_date',
        'file_modified_date_local',
        'file_name',
        'filename',
        'filename_last',
        'filenameextension',
        'filenameextension_last',
        'folder',
        'foldername',
        'foldername_last',
        'isrc',
        'keywords',
        'label',
        'lyrics',
        'movie',
        'movie_more',
        'name',
        'part',
        'performer',
        'producer',
        'mastered_date',
        'next_segment_uid',
        'previous_segment_uid',
        'recorded_date',
        'segment_filename',
        'segment_uid',
        'show',
        'string',
        'summary',
        'synopsis',
        'tagged_date',
        'title',
        'track_more',
        'track_name',
        'uid',
        'uniqueid',
        'uniqueid_string',
        'writtenby',
    }
)

#: Free text in knowit's own parsed output.
PARSED_TEXT_KEYS = frozenset({'name', 'path', 'title'})

#: Subtrees that describe knowit itself and must survive redaction intact.
PARSED_SKIP_KEYS = frozenset({'provider'})

#: Subtrees whose every string value is free text, whatever the key is called.
OPAQUE_SUBTREE_KEYS = frozenset({'extra', 'tags'})

#: Technical values in those subtrees. knowit reads them, and they tell nothing about the content.
#: An old mkvmerge adds the language to the key: `BPS-eng`.
TECHNICAL_TAG_KEYS = frozenset({'language', 'bps', 'duration', 'number_of_frames', 'number_of_bytes', 'mimetype'})


def mask_text(value: str) -> str:
    """Mask free text while keeping its shape.

    Letters and digits of every script are replaced, so the wording is gone. Separators,
    symbols, and combining marks are kept verbatim.
    """
    masked = []
    for char in value:
        if char.isnumeric():
            masked.append('0')
        elif char.isalpha():
            masked.append('x')
        else:
            masked.append(char)
    return ''.join(masked)


def redact(
    data: typing.Any,
    keys: typing.AbstractSet[str],
    skip_keys: typing.AbstractSet[str] = frozenset(),
    mask_everything: bool = False,
) -> typing.Any:
    """Return a copy of `data` with free text masked."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            lowered = str(key).lower()
            if lowered in skip_keys or (lowered.split('-')[0] in TECHNICAL_TAG_KEYS and isinstance(value, str)):
                result[key] = value
            elif lowered in OPAQUE_SUBTREE_KEYS:
                result[key] = redact(value, keys, skip_keys, mask_everything=True)
            else:
                result[key] = redact(value, keys, skip_keys, mask_everything or lowered in keys)
        return result

    if isinstance(data, list):
        return [redact(item, keys, skip_keys, mask_everything) for item in data]

    if mask_everything and isinstance(data, str):
        return mask_text(data)

    # mkvmerge gives the track uid as a number
    if mask_everything and isinstance(data, int) and not isinstance(data, bool):
        return 0

    return data


def mask_path(data: typing.Any, path: str) -> typing.Any:
    """Return a copy of `data` with the path, its folder, and its file name masked in every string.

    The error messages of the backends quote the path, and no key tells where.
    """
    if isinstance(data, dict):
        return {key: mask_path(value, path) for key, value in data.items()}

    if isinstance(data, list):
        return [mask_path(item, path) for item in data]

    if isinstance(data, str):
        for part in (path, os.path.dirname(path), os.path.basename(path)):
            if part.strip('/\\.'):
                data = data.replace(part, mask_text(part))

    return data


def mask_home(data: typing.Any, home: str | None = None) -> typing.Any:
    """Return a copy of `data` with the home folder replaced by `~` in every key and string.

    The locations of Python, knowit, and the backends, and the tracebacks, often start with
    the home folder, and it holds the user name. A location is a key in the provider versions.
    """
    home = os.path.expanduser('~') if home is None else home
    if not home.strip('/\\'):
        return data

    if isinstance(data, dict):
        return {mask_home(key, home): mask_home(value, home) for key, value in data.items()}

    if isinstance(data, list):
        return [mask_home(item, home) for item in data]

    if isinstance(data, str):
        return '~' if data == home else data.replace(home + os.sep, '~' + os.sep)

    return data


def describe_path(path: str | os.PathLike[str], anonymize: bool = True) -> dict[str, typing.Any]:
    """Describe a path in a way that is safe to publish but keeps the failing detail.

    For the most common class of report -- "knowit cannot open this file" -- the path is
    the bug. This keeps the encoding facts needed to reproduce it, and the symbols that
    can trigger it, without disclosing the title.
    """
    text = os.fspath(path)
    directory, basename = os.path.split(text)
    mask = mask_text if anonymize else str

    non_ascii = {char for char in text if not char.isascii()}
    filesystem_encoding = sys.getfilesystemencoding()
    try:
        text.encode(filesystem_encoding)
        encodable = True
    except UnicodeError:
        encodable = False

    info: dict[str, typing.Any] = {
        'directory': mask(directory),
        'basename': mask(basename),
        'basename_repr': ascii(mask(basename)),
        'length': len(text),
        'non_ascii': sorted({_describe_char(char, anonymize) for char in non_ascii}),
        'is_nfc': unicodedata.is_normalized('NFC', text),
        'is_nfd': unicodedata.is_normalized('NFD', text),
        'has_surrogates': any(0xD800 <= ord(char) <= 0xDFFF for char in text),
        'filesystem_encoding': filesystem_encoding,
        'encodable_to_filesystem_encoding': encodable,
    }

    try:
        info['exists'] = os.path.exists(text)
        info['is_file'] = os.path.isfile(text)
        info['readable'] = os.access(text, os.R_OK)
        if info['is_file']:
            info['size'] = os.path.getsize(text)
    except OSError as error:
        info['stat_error'] = f'{type(error).__name__}: {error}'

    return info


def _describe_char(char: str, anonymize: bool = False) -> str:
    """Return a printable identity for a character, usable in a public issue."""
    if anonymize and char.isnumeric():
        return 'non-ascii number'
    if anonymize and char.isalpha():
        return 'non-ascii letter'
    name = unicodedata.name(char, '<unnamed>')
    return f'U+{ord(char):04X} {name}'


def _raw_data(context: typing.Mapping[str, typing.Any]) -> typing.Any:
    """Return the backend's raw output as structured data."""
    debug_data = context.get('debug_data')
    if not callable(debug_data):
        return None
    try:
        dumped = debug_data()
    except Exception:
        return {'error': traceback.format_exc()}
    try:
        return json.loads(dumped)
    except ValueError:
        return dumped


def probe_provider(
    name: str,
    video_path: str,
    context: typing.Mapping[str, typing.Any],
    anonymize: bool = True,
) -> dict[str, typing.Any]:
    """Run a single backend and capture whatever it produced, failure included."""
    result: dict[str, typing.Any] = {}
    provider = api.available_providers.get(name)
    if provider is None:
        return {'status': 'unavailable'}

    result['location'] = getattr(provider.executor, 'location', None) or name
    if not provider.loaded():
        result['status'] = 'not installed'
        return result
    if not provider.accepts(video_path):
        result['status'] = 'does not accept this file'
        return result

    probe_context: dict[str, typing.Any] = {**context, 'profile': 'code'}
    parsed = None
    try:
        parsed = provider.describe(video_path, probe_context)
        result['status'] = 'ok'
    except Exception:
        result['status'] = 'error'
        result['traceback'] = traceback.format_exc()

    raw = _raw_data(probe_context)
    if raw is not None:
        result['raw'] = redact(raw, RAW_TEXT_KEYS) if anonymize else raw
    if parsed:
        result['parsed'] = redact(parsed, PARSED_TEXT_KEYS, PARSED_SKIP_KEYS) if anonymize else parsed

    return result


def build_media_report(
    video_path: str | os.PathLike[str],
    context: typing.Mapping[str, typing.Any] | None = None,
    anonymize: bool = True,
) -> dict[str, typing.Any]:
    """Build the per-file part of a report, probing every installed backend."""
    context = dict(context or {})
    context.setdefault('profile', 'code')
    text = os.fspath(video_path)

    report: dict[str, typing.Any] = {'path': describe_path(text, anonymize)}
    try:
        api.initialize(context)
    except Exception:
        report['initialization_error'] = traceback.format_exc()
        return report

    providers = {}
    for name in api.provider_names:
        try:
            providers[name] = probe_provider(name, text, context, anonymize)
        except Exception:
            providers[name] = {'status': 'error', 'traceback': traceback.format_exc()}
    report['providers'] = mask_path(providers, text) if anonymize else providers

    return report


def build_report(
    video_paths: typing.Iterable[str | os.PathLike[str]] = (),
    context: typing.Mapping[str, typing.Any] | None = None,
    anonymize: bool = True,
) -> dict[str, typing.Any]:
    """Build a complete bug report. This never raises: a partial report still helps."""
    context = dict(context or {})
    report: dict[str, typing.Any] = {
        'knowit_bug_report': REPORT_VERSION,
        'generated_at': datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        'knowit_version': __version__,
        'anonymized': anonymize,
    }

    try:
        report['environment'] = collect_environment(context)
    except Exception:
        report['environment'] = {'error': traceback.format_exc()}

    media = []
    for video_path in video_paths:
        try:
            media.append(build_media_report(video_path, context, anonymize))
        except Exception:
            error = {'error': traceback.format_exc()}
            media.append(mask_path(error, os.fspath(video_path)) if anonymize else error)
    if media:
        report['media'] = media

    return mask_home(report) if anonymize else report


def dump_report(report: typing.Mapping[str, typing.Any]) -> str:
    """Render a report as YAML, using the same value formatting as the fixtures."""
    return yaml.dump(
        dict(report),
        Dumper=get_yaml_dumper({'profile': 'code'}),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def default_output_path() -> str:
    """Return the file a report is written to when no destination is given.

    The name never repeats the media name: the report masks titles, so putting one in
    the file name the user uploads would defeat that.
    """
    return 'knowit-report.yml'
