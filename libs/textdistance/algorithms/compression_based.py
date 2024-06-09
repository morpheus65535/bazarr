from __future__ import annotations

# built-in
import codecs
import math
from collections import Counter
from fractions import Fraction
from itertools import groupby, permutations
from typing import Any, Sequence, TypeVar

# app
from .base import Base as _Base


try:
    # built-in
    import lzma
except ImportError:
    lzma = None  # type: ignore[assignment]


__all__ = [
    'ArithNCD', 'LZMANCD', 'BZ2NCD', 'RLENCD', 'BWTRLENCD', 'ZLIBNCD',
    'SqrtNCD', 'EntropyNCD',

    'bz2_ncd', 'lzma_ncd', 'arith_ncd', 'rle_ncd', 'bwtrle_ncd', 'zlib_ncd',
    'sqrt_ncd', 'entropy_ncd',
]
T = TypeVar('T')


class _NCDBase(_Base):
    """Normalized compression distance (NCD)

    https://articles.orsinium.dev/other/ncd/
    https://en.wikipedia.org/wiki/Normalized_compression_distance#Normalized_compression_distance
    """
    qval = 1

    def __init__(self, qval: int = 1) -> None:
        self.qval = qval

    def maximum(self, *sequences) -> int:
        return 1

    def _get_size(self, data: str) -> float:
        return len(self._compress(data))

    def _compress(self, data: str) -> Any:
        raise NotImplementedError

    def __call__(self, *sequences) -> float:
        if not sequences:
            return 0
        sequences = self._get_sequences(*sequences)

        concat_len = float('Inf')
        empty = type(sequences[0])()
        for mutation in permutations(sequences):
            if isinstance(empty, (str, bytes)):
                data = empty.join(mutation)
            else:
                data = sum(mutation, empty)
            concat_len = min(concat_len, self._get_size(data))  # type: ignore[arg-type]

        compressed_lens = [self._get_size(s) for s in sequences]
        max_len = max(compressed_lens)
        if max_len == 0:
            return 0
        return (concat_len - min(compressed_lens) * (len(sequences) - 1)) / max_len


class _BinaryNCDBase(_NCDBase):

    def __init__(self) -> None:
        pass

    def __call__(self, *sequences) -> float:
        if not sequences:
            return 0
        if isinstance(sequences[0], str):
            sequences = tuple(s.encode('utf-8') for s in sequences)
        return super().__call__(*sequences)


class ArithNCD(_NCDBase):
    """Arithmetic coding

    https://github.com/gw-c/arith
    http://www.drdobbs.com/cpp/data-compression-with-arithmetic-encodin/240169251
    https://en.wikipedia.org/wiki/Arithmetic_coding
    """

    def __init__(self, base: int = 2, terminator: str | None = None, qval: int = 1) -> None:
        self.base = base
        self.terminator = terminator
        self.qval = qval

    def _make_probs(self, *sequences) -> dict[str, tuple[Fraction, Fraction]]:
        """
        https://github.com/gw-c/arith/blob/master/arith.py
        """
        sequences = self._get_counters(*sequences)
        counts = self._sum_counters(*sequences)
        if self.terminator is not None:
            counts[self.terminator] = 1
        total_letters = sum(counts.values())

        prob_pairs = {}
        cumulative_count = 0
        for char, current_count in counts.most_common():
            prob_pairs[char] = (
                Fraction(cumulative_count, total_letters),
                Fraction(current_count, total_letters),
            )
            cumulative_count += current_count
        assert cumulative_count == total_letters
        return prob_pairs

    def _get_range(
        self,
        data: str,
        probs: dict[str, tuple[Fraction, Fraction]],
    ) -> tuple[Fraction, Fraction]:
        if self.terminator is not None:
            if self.terminator in data:
                data = data.replace(self.terminator, '')
            data += self.terminator

        start = Fraction(0, 1)
        width = Fraction(1, 1)
        for char in data:
            prob_start, prob_width = probs[char]
            start += prob_start * width
            width *= prob_width
        return start, start + width

    def _compress(self, data: str) -> Fraction:
        probs = self._make_probs(data)
        start, end = self._get_range(data=data, probs=probs)
        output_fraction = Fraction(0, 1)
        output_denominator = 1
        while not (start <= output_fraction < end):
            output_numerator = 1 + ((start.numerator * output_denominator) // start.denominator)
            output_fraction = Fraction(output_numerator, output_denominator)
            output_denominator *= 2
        return output_fraction

    def _get_size(self, data: str) -> int:
        numerator = self._compress(data).numerator
        if numerator == 0:
            return 0
        return math.ceil(math.log(numerator, self.base))


class RLENCD(_NCDBase):
    """Run-length encoding

    https://en.wikipedia.org/wiki/Run-length_encoding
    """

    def _compress(self, data: Sequence) -> str:
        new_data = []
        for k, g in groupby(data):
            n = len(list(g))
            if n > 2:
                new_data.append(str(n) + k)
            elif n == 1:
                new_data.append(k)
            else:
                new_data.append(2 * k)
        return ''.join(new_data)


class BWTRLENCD(RLENCD):
    """
    https://en.wikipedia.org/wiki/Burrows%E2%80%93Wheeler_transform
    https://en.wikipedia.org/wiki/Run-length_encoding
    """

    def __init__(self, terminator: str = '\0') -> None:
        self.terminator: Any = terminator

    def _compress(self, data: str) -> str:
        if not data:
            data = self.terminator
        elif self.terminator not in data:
            data += self.terminator
            modified = sorted(data[i:] + data[:i] for i in range(len(data)))
            empty = type(data)()
            data = empty.join(subdata[-1] for subdata in modified)
        return super()._compress(data)


# -- NORMAL COMPRESSORS -- #


class SqrtNCD(_NCDBase):
    """Square Root based NCD

    Size of compressed data equals to sum of square roots of counts of every
    element in the input sequence.
    """

    def __init__(self, qval: int = 1) -> None:
        self.qval = qval

    def _compress(self, data: Sequence[T]) -> dict[T, float]:
        return {element: math.sqrt(count) for element, count in Counter(data).items()}

    def _get_size(self, data: Sequence) -> float:
        return sum(self._compress(data).values())


class EntropyNCD(_NCDBase):
    """Entropy based NCD

    Get Entropy of input sequence as a size of compressed data.

    https://en.wikipedia.org/wiki/Entropy_(information_theory)
    https://en.wikipedia.org/wiki/Entropy_encoding
    """

    def __init__(self, qval: int = 1, coef: int = 1, base: int = 2) -> None:
        self.qval = qval
        self.coef = coef
        self.base = base

    def _compress(self, data: Sequence) -> float:
        total_count = len(data)
        entropy = 0.0
        for element_count in Counter(data).values():
            p = element_count / total_count
            entropy -= p * math.log(p, self.base)
        assert entropy >= 0
        return entropy

        # # redundancy:
        # unique_count = len(counter)
        # absolute_entropy = math.log(unique_count, 2) / unique_count
        # return absolute_entropy - entropy / unique_count

    def _get_size(self, data: Sequence) -> float:
        return self.coef + self._compress(data)


# -- BINARY COMPRESSORS -- #


class BZ2NCD(_BinaryNCDBase):
    """
    https://en.wikipedia.org/wiki/Bzip2
    """

    def _compress(self, data: str | bytes) -> bytes:
        return codecs.encode(data, 'bz2_codec')[15:]


class LZMANCD(_BinaryNCDBase):
    """
    https://en.wikipedia.org/wiki/LZMA
    """

    def _compress(self, data: bytes) -> bytes:
        if not lzma:
            raise ImportError('Please, install the PylibLZMA module')
        return lzma.compress(data)[14:]


class ZLIBNCD(_BinaryNCDBase):
    """
    https://en.wikipedia.org/wiki/Zlib
    """

    def _compress(self, data: str | bytes) -> bytes:
        return codecs.encode(data, 'zlib_codec')[2:]


arith_ncd = ArithNCD()
bwtrle_ncd = BWTRLENCD()
bz2_ncd = BZ2NCD()
lzma_ncd = LZMANCD()
rle_ncd = RLENCD()
zlib_ncd = ZLIBNCD()
sqrt_ncd = SqrtNCD()
entropy_ncd = EntropyNCD()
