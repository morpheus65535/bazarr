"""Owner of the model-artifacts file format, write side and read side.

The model artifacts are the digest-locked file set the trainer produces as
one unit: ``models.bin`` (``CMD2``: per-model names and L2 norms, then
zlib-compressed dense bigram tables), ``rowmax.bin`` (``CRM1``: per-model
row maxima for upper-bound prescreening, digest-locked to the
``models.bin`` they were computed from), ``idf.bin`` (a 65536-byte
quantized IDF table), and ``langnorm.bin`` (``CLN1``: per-model norms
under the IDF-weighted metric the language tiers score in, digest-locked
like ``rowmax.bin``).  Keeping both directions in one module means a
format change cannot land on one side only: ``scripts/train.py`` calls
:func:`write_model_artifacts` and :func:`read_models`, while
:mod:`chardet.models` calls :func:`parse_models_bin` and
:func:`parse_rowmax_bin` behind its cached accessors.

Note: ``from __future__ import annotations`` is intentionally omitted
because this module is compiled with mypyc, which does not support PEP 563
string annotations.
"""

import hashlib
import math
import struct
import zlib
from pathlib import Path

#: models.bin magic: the v2 dense zlib-compressed format.
MODELS_MAGIC = b"CMD2"
#: rowmax.bin layout: magic, SHA-256 of the matching models.bin, then one
#: 256-byte row-maxima table per model in models.bin header order.
ROWMAX_MAGIC = b"CRM1"
ROWMAX_HEADER_SIZE = 4 + 32
#: langnorm.bin layout: magic, SHA-256 of the matching models.bin, then one
#: big-endian float64 per model in models.bin header order: the model's
#: L2 norm after each weight is scaled by the square root of its bigram's
#: IDF (see :func:`langnorm_from_table`).
LANGNORM_MAGIC = b"CLN1"
LANGNORM_HEADER_SIZE = 4 + 32

_unpack_uint32 = struct.Struct(">I").unpack_from
_unpack_float64 = struct.Struct(">d").unpack_from


def _decompress_tables(
    data: bytes, offset: int, names: list[str], chunk_size: int = 262144
) -> dict[str, bytes]:
    """Decompress the model tables from ``data[offset:]``, one per name.

    Each model is stored as its own bytes object rather than a memoryview
    slice of one big blob: mypyc compiles bytes indexing in the scoring hot
    loop to a native C array access, while memoryview indexing goes through
    a boxed generic call.  Decompression is incremental, one 64 KB table at
    a time — materializing the whole multi-megabyte blob and slicing it
    would transiently double the allocation and strand the freed pages in
    process RSS.  Trailing compressed bytes are ignored, as with whole-blob
    ``zlib.decompress``; the decompressed size is validated instead.

    :raises ValueError: If the decompressed size is not exactly
        ``len(names) * 65536``.
    """
    num_models = len(names)
    expected_size = num_models * 65536
    decomp = zlib.decompressobj()
    models: dict[str, bytes] = {}
    table = bytearray()
    produced = 0
    pos = offset
    end = len(data)
    flushed = False
    while len(models) < num_models:
        need = 65536 - len(table)
        if decomp.unconsumed_tail:
            piece = decomp.decompress(decomp.unconsumed_tail, need)
        elif pos < end:
            chunk = data[pos : pos + chunk_size]
            pos += len(chunk)
            piece = decomp.decompress(chunk, need)
        elif not flushed:
            flushed = True
            piece = decomp.flush()
            if not piece:
                break  # stream exhausted early -> size mismatch below
        else:
            break  # stream exhausted early -> size mismatch below
        produced += len(piece)
        table += piece
        if len(table) == 65536:
            models[names[len(models)]] = bytes(table)
            table.clear()
        # Unreachable with CPython's zlib — decompress() pieces are capped at
        # ``need``, and a flush() strand (the tail of one back-reference cut
        # mid-copy, at most 258 bytes) only ever lands in a fresh table —
        # but a decompressor that flushed more than asked must not corrupt
        # the table split silently.
        elif len(table) > 65536:  # pragma: no cover
            break  # oversized flush -> size mismatch below
    if len(models) == num_models:
        # Drain any leftover decompressed output so extra data is caught,
        # including surplus tables in compressed input not yet fed to the
        # decompressor.  Bytes after the stream's end marker (decomp.eof)
        # are ignored, matching whole-blob zlib.decompress behavior.
        extra = b""
        if decomp.unconsumed_tail:
            extra = decomp.decompress(decomp.unconsumed_tail, 1)
        while not extra and not decomp.eof and pos < end:
            chunk = data[pos : pos + chunk_size]
            pos += len(chunk)
            extra = decomp.decompress(chunk, 1)
        if not extra and not decomp.eof and not flushed:
            extra = decomp.flush()
        produced += len(extra)
    if produced != expected_size or len(models) != num_models:
        msg = (
            f"corrupt models.bin: decompressed size {produced} "
            f"!= expected {expected_size}"
        )
        raise ValueError(msg)
    return models


def parse_models_bin(
    data: bytes,
) -> tuple[dict[str, bytes], dict[str, float]]:
    """Parse the v2 dense zlib-compressed models.bin format.

    :param data: Raw bytes of models.bin (must be non-empty).
    :returns: A ``(models, norms)`` tuple.
    :raises ValueError: If the data is corrupt or truncated.
    """
    try:
        if data[:4] != MODELS_MAGIC:
            msg = "corrupt models.bin: missing CMD2 magic"
            raise ValueError(msg)

        offset = 4  # skip magic
        (num_models,) = _unpack_uint32(data, offset)
        offset += 4

        if num_models > 10_000:
            msg = f"corrupt models.bin: num_models={num_models} exceeds limit"
            raise ValueError(msg)

        names: list[str] = []
        norms: dict[str, float] = {}
        for _ in range(num_models):
            (name_len,) = _unpack_uint32(data, offset)
            offset += 4
            if name_len > 256:
                msg = f"corrupt models.bin: name_len={name_len} exceeds 256"
                raise ValueError(msg)
            name = data[offset : offset + name_len].decode("utf-8")
            offset += name_len
            (norm,) = _unpack_float64(data, offset)
            offset += 8
            names.append(name)
            norms[name] = norm

        models = _decompress_tables(data, offset, names)

    except zlib.error as e:
        msg = f"corrupt models.bin: {e}"
        raise ValueError(msg) from e
    except (struct.error, UnicodeDecodeError) as e:
        msg = f"corrupt models.bin: {e}"
        raise ValueError(msg) from e

    return models, norms


def parse_rowmax_bin(
    data: bytes, models_digest: bytes, model_keys: list[str]
) -> dict[str, bytes] | None:
    """Parse rowmax.bin into per-model row-maxima tables.

    :param data: Raw bytes of rowmax.bin.
    :param models_digest: SHA-256 digest of the current models.bin bytes.
    :param model_keys: Model keys in models.bin header order.
    :returns: Mapping of model key to its 256-byte row-maxima table, or
        ``None`` when the magic, digest, or size does not match — a stale
        or mismatched file would silently under-estimate row maxima and
        break the upper bound that prescreening depends on.
    """
    if (
        data[:4] == ROWMAX_MAGIC
        and data[4:ROWMAX_HEADER_SIZE] == models_digest
        and len(data) == ROWMAX_HEADER_SIZE + len(model_keys) * 256
    ):
        return {
            key: data[ROWMAX_HEADER_SIZE + i * 256 : ROWMAX_HEADER_SIZE + (i + 1) * 256]
            for i, key in enumerate(model_keys)
        }
    return None


def parse_langnorm_bin(
    data: bytes, models_digest: bytes, model_keys: list[str]
) -> dict[str, float] | None:
    """Parse langnorm.bin into per-model language-scoring norms.

    :param data: Raw bytes of langnorm.bin.
    :param models_digest: SHA-256 digest of the current models.bin bytes.
    :param model_keys: Model keys in models.bin header order.
    :returns: Mapping of model key to its IDF-weighted norm, or ``None``
        when the magic, digest, or size does not match -- a stale file
        would normalize every language score against the wrong length and
        silently tilt the comparison between languages.
    """
    if (
        data[:4] == LANGNORM_MAGIC
        and data[4:LANGNORM_HEADER_SIZE] == models_digest
        and len(data) == LANGNORM_HEADER_SIZE + len(model_keys) * 8
    ):
        return {
            key: _unpack_float64(data, LANGNORM_HEADER_SIZE + i * 8)[0]
            for i, key in enumerate(model_keys)
        }
    return None


def langnorm_from_table(table: bytes, idf: bytes) -> float:
    """Derive one model's norm under the language-scoring metric.

    The language tiers compare an input profile weighted by IDF against
    models weighted by the square root of IDF, so a model's length in that
    space is the root of the sum of ``weight**2 * idf`` over its bigrams.
    Scoring folds the model-side factor into the profile and divides by
    this norm, so the table itself is never rescaled.
    """
    total = 0
    for i in range(65536):
        v = table[i]
        if v:
            total += v * v * idf[i]
    return math.sqrt(total)


def rowmax_from_table(table: bytes) -> bytes:
    """Derive the 256-byte row-maxima table of one dense model table.

    Entry ``b1`` holds the maximum weight in the model's row for lead byte
    ``b1``; a row with no bigrams yields 0.
    """
    return bytes(max(table[start : start + 256]) for start in range(0, 65536, 256))


def read_models(models_path: Path) -> dict[str, dict[tuple[int, int], int]]:
    """Read models.bin into the sparse per-model bigram dicts training uses.

    The inverse of :func:`write_model_artifacts`'s models.bin output: only
    non-zero weights appear in the dicts.  A missing or empty file reads as
    no models, so a first-ever training run and a full retrain look the
    same to the caller.

    :returns: Mapping of model key to ``{(b1, b2): weight}``.
    :raises ValueError: If the file exists but is corrupt.
    """
    if not models_path.is_file():
        return {}
    data = models_path.read_bytes()
    if not data:
        return {}
    tables, _norms = parse_models_bin(data)
    models: dict[str, dict[tuple[int, int], int]] = {}
    for name, table in tables.items():
        bigrams: dict[tuple[int, int], int] = {}
        for idx in range(65536):
            weight = table[idx]
            if weight > 0:
                bigrams[(idx >> 8, idx & 0xFF)] = weight
        models[name] = bigrams
    return models


def _idf_table(models: dict[str, dict[tuple[int, int], int]]) -> bytes:
    """Compute the 65536-byte quantized IDF table over all models.

    For each bigram index the byte holds a scaled inverse document
    frequency: bigrams present in every model score 1 (minimal signal),
    bigrams in exactly one model score 255 (maximum signal), and bigrams
    in no model score 1 (unknown, neutral).
    """
    num_models = len(models)
    doc_freq = [0] * 65536
    for bigrams in models.values():
        for b1, b2 in bigrams:
            doc_freq[(b1 << 8) | b2] += 1
    max_idf = math.log(num_models) if num_models > 1 else 1.0
    scale = 254.0 / max_idf if max_idf > 0 else 0.0
    idf_table = bytearray(65536)
    for idx in range(65536):
        df = doc_freq[idx]
        if df > 0:
            idf_val = math.log(num_models / df)
            idf_table[idx] = max(1, round(idf_val * scale) + 1)
        else:
            idf_table[idx] = 1
    return bytes(idf_table)


def write_model_artifacts(
    models: dict[str, dict[tuple[int, int], int]],
    models_path: Path,
) -> dict[str, int]:
    """Write the model artifacts as one digest-locked set.

    ``models.bin`` is written at *models_path* (whatever its basename);
    ``rowmax.bin`` and ``idf.bin`` are written beside it under their fixed
    names.  ``rowmax.bin`` embeds the SHA-256 of the exact ``models.bin``
    bytes written here and is deliberately written **last**: it is the
    commit marker for the whole set, so an interrupted run leaves a digest
    mismatch that :func:`parse_rowmax_bin` rejects at load time instead of
    a silently stale sibling (``idf.bin`` is validated by size only).

    :param models: Mapping of model key to sparse ``{(b1, b2): weight}``.
    :param models_path: Destination path for models.bin.
    :returns: Sizes in bytes, keyed by canonical artifact name
        (``models.bin``, ``rowmax.bin``, ``idf.bin``, ``langnorm.bin``).
    """
    models_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_names = sorted(models)
    idf_table = _idf_table(models)

    header = bytearray(MODELS_MAGIC)
    header += struct.pack("!I", len(sorted_names))
    tables = bytearray()
    rowmax_rows: list[bytes] = []
    langnorms: list[float] = []
    for name in sorted_names:
        # Expand sparse dict to dense 65536-byte table and compute L2 norm
        table = bytearray(65536)
        sq_sum = 0
        for (b1, b2), weight in models[name].items():
            table[(b1 << 8) | b2] = weight
            sq_sum += weight * weight
        name_bytes = name.encode("utf-8")
        header += struct.pack("!I", len(name_bytes)) + name_bytes
        header += struct.pack("!d", math.sqrt(sq_sum))
        # Freeze once and derive the row maxima from the exact bytes being
        # serialized, so the two can never describe different tables.
        frozen = bytes(table)
        tables += frozen
        rowmax_rows.append(rowmax_from_table(frozen))
        langnorms.append(langnorm_from_table(frozen, idf_table))

    models_blob = bytes(header) + zlib.compress(bytes(tables), 9)
    models_path.write_bytes(models_blob)
    models_digest = hashlib.sha256(models_blob).digest()

    models_path.with_name("idf.bin").write_bytes(idf_table)

    rowmax_blob = bytearray(ROWMAX_MAGIC)
    rowmax_blob += models_digest
    for row in rowmax_rows:
        rowmax_blob += row
    models_path.with_name("rowmax.bin").write_bytes(rowmax_blob)

    langnorm_blob = langnorm_blob_for(langnorms, models_digest)
    models_path.with_name("langnorm.bin").write_bytes(langnorm_blob)

    return {
        "models.bin": len(models_blob),
        "rowmax.bin": len(rowmax_blob),
        "idf.bin": len(idf_table),
        "langnorm.bin": len(langnorm_blob),
    }


def langnorm_blob_for(langnorms: list[float], models_digest: bytes) -> bytes:
    """Serialize langnorm.bin for norms in models.bin header order."""
    blob = bytearray(LANGNORM_MAGIC)
    blob += models_digest
    for norm in langnorms:
        blob += struct.pack("!d", norm)
    return bytes(blob)
