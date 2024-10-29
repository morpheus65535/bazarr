from __future__ import annotations

# built-in
from functools import reduce
from itertools import islice, permutations, repeat
from math import log
from typing import Sequence

# app
from .base import Base as _Base, BaseSimilarity as _BaseSimilarity
from .edit_based import DamerauLevenshtein


__all__ = [
    'Jaccard', 'Sorensen', 'Tversky',
    'Overlap', 'Cosine', 'Tanimoto', 'MongeElkan', 'Bag',

    'jaccard', 'sorensen', 'tversky', 'sorensen_dice', 'dice',
    'overlap', 'cosine', 'tanimoto', 'monge_elkan', 'bag',
]


class Jaccard(_BaseSimilarity):
    """
    Compute the Jaccard similarity between the two sequences.
    They should contain hashable items.
    The return value is a float between 0 and 1, where 1 means equal,
    and 0 totally different.

    https://en.wikipedia.org/wiki/Jaccard_index
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/jaccard.js
    """

    def __init__(
        self,
        qval: int = 1,
        as_set: bool = False,
        external: bool = True,
    ) -> None:
        self.qval = qval
        self.as_set = as_set
        self.external = external

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> float:
        result = self.quick_answer(*sequences)
        if result is not None:
            return result

        sequences = self._get_counters(*sequences)               # sets
        intersection = self._intersect_counters(*sequences)      # set
        intersection = self._count_counters(intersection)        # int
        union = self._union_counters(*sequences)                 # set
        union = self._count_counters(union)                      # int
        return intersection / union


class Sorensen(_BaseSimilarity):
    """
    Compute the Sorensen distance between the two sequences.
    They should contain hashable items.
    The return value is a float between 0 and 1, where 0 means equal,
    and 1 totally different.

    https://en.wikipedia.org/wiki/S%C3%B8rensen%E2%80%93Dice_coefficient
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/dice.js
    """

    def __init__(self, qval: int = 1, as_set: bool = False, external: bool = True) -> None:
        self.qval = qval
        self.as_set = as_set
        self.external = external

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> float:
        result = self.quick_answer(*sequences)
        if result is not None:
            return result

        sequences = self._get_counters(*sequences)               # sets
        count = sum(self._count_counters(s) for s in sequences)
        intersection = self._intersect_counters(*sequences)      # set
        intersection = self._count_counters(intersection)        # int
        return 2.0 * intersection / count


class Tversky(_BaseSimilarity):
    """Tversky index

    https://en.wikipedia.org/wiki/Tversky_index
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/tversky.js
    """

    def __init__(
        self,
        qval: int = 1,
        ks: Sequence[float] = None,
        bias: float | None = None,
        as_set: bool = False,
        external: bool = True,
    ) -> None:
        self.qval = qval
        self.ks = ks or repeat(1)
        self.bias = bias
        self.as_set = as_set
        self.external = external

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> float:
        quick_result = self.quick_answer(*sequences)
        if quick_result is not None:
            return quick_result

        sequences = self._get_counters(*sequences)                # sets
        intersection = self._intersect_counters(*sequences)       # set
        intersection = self._count_counters(intersection)         # int
        sequences = [self._count_counters(s) for s in sequences]  # ints
        ks = list(islice(self.ks, len(sequences)))

        if len(sequences) != 2 or self.bias is None:
            result = intersection
            for k, s in zip(ks, sequences):
                result += k * (s - intersection)
            return intersection / result

        s1, s2 = sequences
        alpha, beta = ks
        a_val = min([s1, s2])
        b_val = max([s1, s2])
        c_val = intersection + self.bias
        result = alpha * beta * (a_val - b_val) + b_val * beta
        return c_val / (result + c_val)


class Overlap(_BaseSimilarity):
    """overlap coefficient

    https://en.wikipedia.org/wiki/Overlap_coefficient
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/overlap.js
    """

    def __init__(
        self,
        qval: int = 1,
        as_set: bool = False,
        external: bool = True,
    ) -> None:
        self.qval = qval
        self.as_set = as_set
        self.external = external

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> float:
        result = self.quick_answer(*sequences)
        if result is not None:
            return result

        sequences = self._get_counters(*sequences)                  # sets
        intersection = self._intersect_counters(*sequences)         # set
        intersection = self._count_counters(intersection)           # int
        sequences = [self._count_counters(s) for s in sequences]    # ints

        return intersection / min(sequences)


class Cosine(_BaseSimilarity):
    """cosine similarity (Ochiai coefficient)

    https://en.wikipedia.org/wiki/Cosine_similarity
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/cosine.js
    """

    def __init__(
        self,
        qval: int = 1,
        as_set: bool = False,
        external: bool = True,
    ) -> None:
        self.qval = qval
        self.as_set = as_set
        self.external = external

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> float:
        result = self.quick_answer(*sequences)
        if result is not None:
            return result

        sequences = self._get_counters(*sequences)                  # sets
        intersection = self._intersect_counters(*sequences)         # set
        intersection = self._count_counters(intersection)           # int
        sequences = [self._count_counters(s) for s in sequences]    # ints
        prod = reduce(lambda x, y: x * y, sequences)

        return intersection / pow(prod, 1.0 / len(sequences))


class Tanimoto(Jaccard):
    """Tanimoto distance
    This is identical to the Jaccard similarity coefficient
    and the Tversky index for alpha=1 and beta=1.
    """

    def __call__(self, *sequences: Sequence) -> float:
        result = super().__call__(*sequences)
        if result == 0:
            return float('-inf')
        else:
            return log(result, 2)


class MongeElkan(_BaseSimilarity):
    """
    https://www.academia.edu/200314/Generalized_Monge-Elkan_Method_for_Approximate_Text_String_Comparison
    http://www.cs.cmu.edu/~wcohen/postscript/kdd-2003-match-ws.pdf
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/monge-elkan.js
    """
    _damerau_levenshtein = DamerauLevenshtein()

    def __init__(
        self,
        algorithm=_damerau_levenshtein,
        symmetric: bool = False,
        qval: int = 1,
        external: bool = True,
    ) -> None:
        self.algorithm = algorithm
        self.symmetric = symmetric
        self.qval = qval
        self.external = external

    def maximum(self, *sequences: Sequence) -> float:
        result = self.algorithm.maximum(sequences)
        for seq in sequences:
            if seq:
                result = max(result, self.algorithm.maximum(*seq))
        return result

    def _calc(self, seq, *sequences: Sequence) -> float:
        if not seq:
            return 0
        maxes = []
        for c1 in seq:
            for s in sequences:
                max_sim = float('-inf')
                for c2 in s:
                    max_sim = max(max_sim, self.algorithm.similarity(c1, c2))
                maxes.append(max_sim)
        return sum(maxes) / len(seq) / len(maxes)

    def __call__(self, *sequences: Sequence) -> float:
        quick_result = self.quick_answer(*sequences)
        if quick_result is not None:
            return quick_result
        sequences = self._get_sequences(*sequences)

        if self.symmetric:
            result = []
            for seqs in permutations(sequences):
                result.append(self._calc(*seqs))
            return sum(result) / len(result)
        else:
            return self._calc(*sequences)


class Bag(_Base):
    """Bag distance
    https://github.com/Yomguithereal/talisman/blob/master/src/metrics/bag.js
    """

    def __call__(self, *sequences: Sequence) -> float:
        sequences = self._get_counters(*sequences)              # sets
        intersection = self._intersect_counters(*sequences)     # set
        return max(self._count_counters(sequence - intersection) for sequence in sequences)


bag = Bag()
cosine = Cosine()
dice = Sorensen()
jaccard = Jaccard()
monge_elkan = MongeElkan()
overlap = Overlap()
sorensen = Sorensen()
sorensen_dice = Sorensen()
# sorensen_dice = Tversky(ks=[.5, .5])
tanimoto = Tanimoto()
tversky = Tversky()
