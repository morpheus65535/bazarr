"""Model loading and bigram scoring utilities.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

import functools
import importlib.resources
import math
import struct
import warnings
import zlib

from chardet.registry import REGISTRY, lookup_encoding

_unpack_uint32 = struct.Struct(">I").unpack_from
_unpack_float64 = struct.Struct(">d").unpack_from
_V2_MAGIC = b"CMD2"

# Encodings that map to exactly one language, derived from the registry.
# Keyed by canonical name only — callers always use canonical names.
_SINGLE_LANG_MAP: dict[str, str] = {}
for _enc in REGISTRY.values():
    if len(_enc.languages) == 1:
        _SINGLE_LANG_MAP[_enc.name] = _enc.languages[0]


def _parse_models_bin(
    data: bytes,
) -> tuple[dict[str, memoryview], dict[str, float]]:
    """Parse the v2 dense zlib-compressed models.bin format.

    :param data: Raw bytes of models.bin (must be non-empty).
    :returns: A ``(models, norms)`` tuple.
    :raises ValueError: If the data is corrupt or truncated.
    """
    try:
        if data[:4] != _V2_MAGIC:
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

        # zlib.decompress is faster than decompressobj; trailing bytes are
        # unlikely in bundled data and would not affect correctness since we
        # validate decompressed size.  train.py uses decompressobj for
        # stricter checking during model generation.
        blob = zlib.decompress(data[offset:])
        expected_size = num_models * 65536
        if len(blob) != expected_size:
            msg = (
                f"corrupt models.bin: decompressed size {len(blob)} "
                f"!= expected {expected_size}"
            )
            raise ValueError(msg)

        # memoryview slices avoid copies; the blob bytes object is kept
        # alive by the functools.cache on _load_models_data().
        mv = memoryview(blob)
        models: dict[str, memoryview] = {}
        for i, name in enumerate(names):
            start = i * 65536
            models[name] = mv[start : start + 65536]

    except zlib.error as e:
        msg = f"corrupt models.bin: {e}"
        raise ValueError(msg) from e
    except (struct.error, UnicodeDecodeError) as e:
        msg = f"corrupt models.bin: {e}"
        raise ValueError(msg) from e

    return models, norms


@functools.cache
def _load_models_data() -> tuple[dict[str, memoryview], dict[str, float]]:
    """Load and parse models.bin, returning (models, norms).

    Cached: only reads from disk on first call.
    """
    ref = importlib.resources.files("chardet.models").joinpath("models.bin")
    data = ref.read_bytes()

    if not data:
        warnings.warn(
            "chardet models.bin is empty — statistical detection disabled; "
            "reinstall chardet to fix",
            RuntimeWarning,
            stacklevel=2,
        )
        return {}, {}

    return _parse_models_bin(data)


def load_models() -> dict[str, memoryview]:
    """Load all bigram models from the bundled models.bin file.

    Each model is a memoryview of length 65536 (256*256).
    Index: (b1 << 8) | b2 -> weight (0-255).

    :returns: A dict mapping model key strings to 65536-byte lookup tables.
    """
    return _load_models_data()[0]


def _build_enc_index(
    models: dict[str, memoryview],
) -> dict[str, list[tuple[str | None, memoryview, str]]]:
    """Build a grouped index from a models dict.

    :param models: Mapping of ``"lang/encoding"`` keys to 65536-byte tables.
    :returns: Mapping of encoding name to ``[(lang, model, model_key), ...]``.
    """
    index: dict[str, list[tuple[str | None, memoryview, str]]] = {}
    for key, model in models.items():
        lang, enc = key.split("/", 1)
        index.setdefault(enc, []).append((lang, model, key))

    # Resolve aliases: if a model key uses a non-canonical name,
    # copy the entry under the canonical name.
    for enc_name in list(index):
        canonical = lookup_encoding(enc_name)
        if canonical is not None and canonical not in index:
            index[canonical] = index[enc_name]

    return index


@functools.cache
def get_enc_index() -> dict[str, list[tuple[str | None, memoryview, str]]]:
    """Return a pre-grouped index mapping encoding name -> [(lang, model, model_key), ...]."""
    return _build_enc_index(load_models())


def infer_language(encoding: str) -> str | None:
    """Return the language for a single-language encoding, or None.

    :param encoding: The canonical encoding name.
    :returns: An ISO 639-1 language code, or ``None`` if the encoding is
        multi-language.
    """
    return _SINGLE_LANG_MAP.get(encoding)


def has_model_variants(encoding: str) -> bool:
    """Return True if the encoding has language variants in the model index.

    :param encoding: The canonical encoding name.
    :returns: ``True`` if bigram models exist for this encoding.
    """
    return encoding in get_enc_index()


def _get_model_norms() -> dict[str, float]:
    """Return cached L2 norms for all models, keyed by model key string."""
    return _load_models_data()[1]


@functools.cache
def get_idf_weights() -> bytearray:
    """Return a 65536-byte IDF weight table for bigram profile construction.

    Loads a precomputed table from ``idf.bin`` (generated at training time).
    For each bigram index, the weight reflects how discriminative that bigram
    is across all models:

    - Bigrams in every model (common ASCII) → weight 1 (minimal signal)
    - Bigrams in one model → weight 255 (maximum signal)
    - Bigrams not in any model → weight 1 (unknown, treat as neutral)
    """
    ref = importlib.resources.files("chardet.models").joinpath("idf.bin")
    data = ref.read_bytes()
    if len(data) != 65536:
        warnings.warn(
            f"chardet idf.bin has wrong size ({len(data)}), "
            "falling back to uniform weights",
            RuntimeWarning,
            stacklevel=2,
        )
        return bytearray(b"\x01" * 65536)
    return bytearray(data)


class BigramProfile:
    """Pre-computed bigram frequency distribution for a data sample.

    Computing this once and reusing it across all models reduces per-model
    scoring from O(n) to O(distinct_bigrams).

    Stores a dense ``freq`` list of length 65536 indexed by bigram index, plus
    a ``nonzero`` list of indices with non-zero frequency for fast iteration.
    Each bigram is weighted by its IDF (inverse document frequency) across all
    models — bigrams unique to few models get high weight, bigrams common to
    all models get weight 1.
    """

    __slots__ = ("freq", "input_norm", "nonzero", "weight_sum")

    def __init__(self, data: bytes) -> None:
        """Compute the bigram frequency distribution for *data*.

        Each bigram is weighted by its IDF (inverse document frequency) across
        all loaded models.  Bigrams unique to few models get high weight;
        bigrams common to all models get weight 1.

        :param data: The raw byte data to profile.
        """
        total_bigrams = len(data) - 1
        if total_bigrams <= 0:
            # Use empty lists (not [0]*65536) to avoid a 256KB allocation
            # for no-op profiles.  Safe because score_with_profile returns
            # early when input_norm == 0.0, so freq is never indexed.
            self.freq: list[int] = []
            self.nonzero: list[int] = []
            self.weight_sum: int = 0
            self.input_norm: float = 0.0
            return

        idf = get_idf_weights()
        freq: list[int] = [0] * 65536
        nonzero: list[int] = []
        w_sum = 0
        for i in range(total_bigrams):
            idx = (data[i] << 8) | data[i + 1]
            w = idf[idx]
            if freq[idx] == 0:
                nonzero.append(idx)
            freq[idx] += w
            w_sum += w
        self.freq = freq
        self.nonzero = nonzero
        self.weight_sum = w_sum
        norm_sq = 0
        for idx in nonzero:
            v = freq[idx]
            norm_sq += v * v
        self.input_norm = math.sqrt(norm_sq)

    @classmethod
    def from_weighted_freq(cls, weighted_freq: dict[int, int]) -> "BigramProfile":
        """Create a BigramProfile from pre-computed weighted frequencies.

        Computes ``weight_sum`` and ``input_norm`` from *weighted_freq* to
        ensure consistency between the stored fields.

        :param weighted_freq: Mapping of bigram index to weighted count.
        :returns: A new :class:`BigramProfile` instance.
        """
        profile = cls(b"")
        freq: list[int] = [0] * 65536
        nonzero: list[int] = []
        for idx, count in weighted_freq.items():
            freq[idx] = count
            if count:
                nonzero.append(idx)
        profile.freq = freq
        profile.nonzero = nonzero
        profile.weight_sum = sum(weighted_freq.values())
        profile.input_norm = math.sqrt(sum(v * v for v in weighted_freq.values()))
        return profile


def score_with_profile(
    profile: BigramProfile, model: bytearray | memoryview, model_key: str = ""
) -> float:
    """Score a pre-computed bigram profile against a single model using cosine similarity."""
    if profile.input_norm == 0.0:
        return 0.0
    norms = _get_model_norms()
    model_norm = norms.get(model_key) if model_key else None
    if model_norm is None:
        sq_sum = 0
        for i in range(65536):
            v = model[i]
            if v:
                sq_sum += v * v
        model_norm = math.sqrt(sq_sum)
    if model_norm == 0.0:
        return 0.0
    dot = 0
    freq = profile.freq
    for idx in profile.nonzero:
        dot += model[idx] * freq[idx]
    return dot / (model_norm * profile.input_norm)


def score_best_language(
    data: bytes,
    encoding: str,
    profile: BigramProfile | None = None,
) -> tuple[float, str | None]:
    """Score data against all language variants of an encoding.

    Returns (best_score, best_language). Uses a pre-grouped index for O(L)
    lookup where L is the number of language variants for the encoding.

    If *profile* is provided, it is reused instead of recomputing the bigram
    frequency distribution from *data*.

    :param data: The raw byte data to score.
    :param encoding: The canonical encoding name to match against.
    :param profile: Optional pre-computed :class:`BigramProfile` to reuse.
    :returns: A ``(score, language)`` tuple with the best cosine-similarity
        score and the corresponding language code (or ``None``).
    """
    if not data and profile is None:
        return 0.0, None

    index = get_enc_index()
    variants = index.get(encoding)
    if variants is None:
        return 0.0, None

    if profile is None:
        profile = BigramProfile(data)

    best_score = 0.0
    best_lang: str | None = None
    for lang, model, model_key in variants:
        s = score_with_profile(profile, model, model_key)
        if s > best_score:
            best_score = s
            best_lang = lang

    return best_score, best_lang
