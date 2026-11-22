"""Reproduce path related problems without the media file that triggered them.

The most frequent reports are not about the content of a file, they are about its name:
a superscript, a fraction, an accent, or a character the file system encoding cannot
represent. Those need the name, not the media. This module writes a small sample under
that name and compares the result against the same sample under a plain ascii name.

Limits: `check_name()` only proves something for names that survive as valid Unicode
text the whole way from the shell to this process. It cannot reproduce a genuinely
invalid byte sequence, such as a name left over from a non-Unicode codepage: those
bytes cannot be typed, pasted into an issue, or even passed through `docker run`,
since all of those require valid UTF-8 too (Docker's own CLI replaces invalid bytes in
its arguments with U+FFFD before the container ever sees them). For that case, ask the
reporter to run `--bug-report` on the real file instead: it discovers the name with
`os.scandir`, which Python decodes with the `surrogateescape` error handler, preserving
undecodable bytes as lone surrogates instead of losing them.

What `check_name()` *can* reproduce is a file system encoding mismatch: run it under a
non-UTF-8 locale (`LC_ALL=C PYTHONUTF8=0`) with a non-ascii name, and
`encodable_to_filesystem_encoding` comes back `False` — the candidate file fails to be
created with a `UnicodeEncodeError`, and the verdict reports it. This mirrors minimal
containers or old environments that never set a UTF-8 locale.
"""

import os
import shutil
import struct
import tempfile
import traceback
import typing

from knowit import api
from knowit.bugreport import describe_path

_EBML = b'\x1a\x45\xdf\xa3'
_SEGMENT = b'\x18\x53\x80\x67'
_SEEK_HEAD = b'\x11\x4d\x9b\x74'
_INFO = b'\x15\x49\xa9\x66'
_TRACKS = b'\x16\x54\xae\x6b'
_CLUSTER = b'\x1f\x43\xb6\x75'


def _vint(value: int) -> bytes:
    """Encode a length as an EBML variable size integer."""
    for length in range(1, 9):
        if value < (1 << (7 * length)) - 1:
            return (value | (1 << (7 * length))).to_bytes(length, 'big')
    raise ValueError(value)


def _uint(value: int) -> bytes:
    """Encode an EBML unsigned integer with the fewest bytes."""
    return b'\x00' if value == 0 else value.to_bytes((value.bit_length() + 7) // 8, 'big')


def _element(element_id: bytes, payload: bytes) -> bytes:
    """Build an EBML element."""
    return element_id + _vint(len(payload)) + payload


def _build_sample_mkv() -> bytes:
    """Build the smallest Matroska file that all four backends read successfully.

    A container header alone is not enough. ffprobe stops at "End of file" and enzyme
    raises "No SeekHead found" when there is no track, which made the name check report
    a failure for both of them whatever the name was. So the sample carries one real
    audio track, one cluster, and a SeekHead.
    """
    header = _element(
        _EBML,
        b''.join(
            (
                _element(b'\x42\x86', _uint(1)),  # EBMLVersion
                _element(b'\x42\xf7', _uint(1)),  # EBMLReadVersion
                _element(b'\x42\xf2', _uint(4)),  # EBMLMaxIDLength
                _element(b'\x42\xf3', _uint(8)),  # EBMLMaxSizeLength
                _element(b'\x42\x82', b'matroska'),  # DocType
                _element(b'\x42\x87', _uint(4)),  # DocTypeVersion
                _element(b'\x42\x85', _uint(2)),  # DocTypeReadVersion
            )
        ),
    )

    info = _element(
        _INFO,
        b''.join(
            (
                _element(b'\x2a\xd7\xb1', _uint(1000000)),  # TimestampScale
                _element(b'\x4d\x80', b'knowit'),  # MuxingApp
                _element(b'\x57\x41', b'knowit'),  # WritingApp
                _element(b'\x44\x89', struct.pack('>f', 100.0)),  # Duration
            )
        ),
    )

    tracks = _element(
        _TRACKS,
        _element(
            b'\xae',  # TrackEntry
            b''.join(
                (
                    _element(b'\xd7', _uint(1)),  # TrackNumber
                    _element(b'\x73\xc5', _uint(1)),  # TrackUID
                    _element(b'\x83', _uint(2)),  # TrackType: audio
                    _element(b'\x86', b'A_PCM/INT/LIT'),  # CodecID, needs no extradata
                    _element(
                        b'\xe1',  # Audio
                        b''.join(
                            (
                                _element(b'\xb5', struct.pack('>f', 8000.0)),  # SamplingFrequency
                                _element(b'\x9f', _uint(1)),  # Channels
                                _element(b'\x62\x64', _uint(16)),  # BitDepth
                            )
                        ),
                    ),
                )
            ),
        ),
    )

    block = _element(b'\xa3', _vint(1) + struct.pack('>h', 0) + b'\x80' + b'\x00\x00' * 400)
    cluster = _element(_CLUSTER, _element(b'\xe7', _uint(0)) + block)

    def seek_head(info_at: int, tracks_at: int, cluster_at: int) -> bytes:
        """Build the SeekHead. Positions are relative to the start of the segment data."""
        entries = b''
        for element_id, position in ((_INFO, info_at), (_TRACKS, tracks_at), (_CLUSTER, cluster_at)):
            entries += _element(
                b'\x4d\xbb',  # Seek
                _element(b'\x53\xab', element_id)  # SeekID
                # A fixed width position keeps the SeekHead the same size in both passes,
                # so the offsets it holds stay correct once they are filled in.
                + _element(b'\x53\xac', position.to_bytes(8, 'big')),  # SeekPosition
            )
        return _element(_SEEK_HEAD, entries)

    head_size = len(seek_head(0, 0, 0))
    info_at = head_size
    tracks_at = info_at + len(info)
    cluster_at = tracks_at + len(tracks)
    head = seek_head(info_at, tracks_at, cluster_at)

    return header + _element(_SEGMENT, head + info + tracks + cluster)


#: A small Matroska file with one audio track, used when the reporter has no file to share.
MINIMAL_MKV = _build_sample_mkv()

#: The name the sample is given as a control, to tell a name problem from a file problem.
CONTROL_NAME = 'knowit-control.mkv'

#: Names that have appeared in reports, kept as a regression matrix.
ADVERSARIAL_NAMES = (
    'The Accountant² (2025).mkv',
    'Naked Gun 33⅓ - The Final Insult (1994).mkv',
    'Jellal vs Oración Seis.mkv',
    'Everyone’s Dignity.mkv',
    'What If… T’Challa Became a Star-Lord.mkv',
    'Umlaute äöüß.mkv',
    "KonoSuba – God's blessing.mkv",
    'café decomposed.mkv',
    'symbols [1080p] + extra.mkv',
    '日本語のタイトル.mkv',
    'Русский.mkv',
    'emoji \U0001f3ac.mkv',
)


def probe_name(
    directory: str,
    name: str,
    sample: bytes,
    context: typing.Mapping[str, typing.Any] | None = None,
) -> dict[str, typing.Any]:
    """Write the sample under `name` and report how each backend copes with it."""
    context = dict(context or {})
    context.setdefault('profile', 'code')

    result: dict[str, typing.Any] = {}
    video_path = os.path.join(directory, name)

    try:
        with open(video_path, 'wb') as stream:
            stream.write(sample)
    except (OSError, UnicodeError):
        result['created'] = False
        result['error'] = traceback.format_exc()
        return result

    result['created'] = True
    result['path'] = describe_path(video_path, anonymize=False)

    api.initialize(context)
    providers: dict[str, typing.Any] = {}
    for provider_name in api.provider_names:
        provider = api.available_providers.get(provider_name)
        if provider is None or not provider.loaded():
            providers[provider_name] = {'status': 'not installed'}
            continue
        if not provider.accepts(video_path):
            providers[provider_name] = {'status': 'does not accept this file'}
            continue

        try:
            provider.describe(video_path, dict(context))
            providers[provider_name] = {'status': 'ok'}
        except Exception as error:
            providers[provider_name] = {
                'status': 'error',
                'error': f'{type(error).__name__}: {error}',
                'traceback': traceback.format_exc(),
            }

    result['providers'] = providers
    return result


def check_name(
    name: str,
    context: typing.Mapping[str, typing.Any] | None = None,
    source: str | os.PathLike[str] | None = None,
) -> dict[str, typing.Any]:
    """Check whether a file name alone makes a backend fail.

    The same bytes are probed twice: once under a plain ascii name, once under `name`.
    A backend that only fails on the second one has a name handling problem. A backend
    that fails on both has a problem with the content, not with the name.
    """
    sample = MINIMAL_MKV
    if source is not None:
        with open(source, 'rb') as stream:
            sample = stream.read()

    directory = tempfile.mkdtemp(prefix='knowit-check-')
    try:
        control = probe_name(directory, CONTROL_NAME, sample, context)
        candidate = probe_name(directory, name, sample, context)
    finally:
        shutil.rmtree(directory, ignore_errors=True)

    return {
        'name': name,
        'sample': 'the file you provided'
        if source is not None
        else f'a generated {len(MINIMAL_MKV)} byte Matroska file with one audio track',
        'control': control,
        'candidate': candidate,
        'verdict': verdict(control, candidate),
    }


def verdict(control: typing.Mapping[str, typing.Any], candidate: typing.Mapping[str, typing.Any]) -> dict[str, str]:
    """Compare both probes and say, per backend, what the result means."""
    if not candidate.get('created'):
        return {'*': 'the file could not be created with this name'}

    result = {}
    control_providers = control.get('providers') or {}
    candidate_providers = candidate.get('providers') or {}
    for provider_name, candidate_result in candidate_providers.items():
        control_status = (control_providers.get(provider_name) or {}).get('status')
        candidate_status = candidate_result.get('status')

        if candidate_status == control_status:
            if candidate_status == 'error':
                result[provider_name] = 'fails with the control name too: the name is not the cause'
            else:
                result[provider_name] = f'{candidate_status}: the name is handled correctly'
        elif candidate_status == 'error':
            result[provider_name] = 'fails with this name only: the name is the problem'
        else:
            result[provider_name] = f'{control_status} -> {candidate_status}'

    return result
