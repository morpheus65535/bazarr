from __future__ import annotations

# built-in
from itertools import takewhile
from typing import Sequence

# app
from .base import Base as _Base, BaseSimilarity as _BaseSimilarity
from .types import SimFunc


__all__ = [
    'Prefix', 'Postfix', 'Length', 'Identity', 'Matrix',
    'prefix', 'postfix', 'length', 'identity', 'matrix',
]


class Prefix(_BaseSimilarity):
    """prefix similarity
    """

    def __init__(self, qval: int = 1, sim_test: SimFunc = None) -> None:
        self.qval = qval
        self.sim_test = sim_test or self._ident

    def __call__(self, *sequences: Sequence) -> Sequence:
        if not sequences:
            return ''
        sequences = self._get_sequences(*sequences)

        def test(seq):
            return self.sim_test(*seq)

        result = [c[0] for c in takewhile(test, zip(*sequences))]

        s = sequences[0]
        if isinstance(s, str):
            return ''.join(result)
        if isinstance(s, bytes):
            return b''.join(result)
        return result

    def similarity(self, *sequences: Sequence) -> int:
        return len(self(*sequences))


class Postfix(Prefix):
    """postfix similarity
    """

    def __call__(self, *sequences: Sequence) -> Sequence:
        s = sequences[0]
        sequences = [list(reversed(s)) for s in sequences]
        result = reversed(super().__call__(*sequences))
        if isinstance(s, str):
            return ''.join(result)
        if isinstance(s, bytes):
            return b''.join(result)
        return list(result)


class Length(_Base):
    """Length distance
    """

    def __call__(self, *sequences: Sequence) -> int:
        lengths = list(map(len, sequences))
        return max(lengths) - min(lengths)


class Identity(_BaseSimilarity):
    """Identity similarity
    """

    def maximum(self, *sequences: Sequence) -> int:
        return 1

    def __call__(self, *sequences: Sequence) -> int:
        return int(self._ident(*sequences))


class Matrix(_BaseSimilarity):
    """Matrix similarity
    """

    def __init__(
        self,
        mat=None,
        mismatch_cost: int = 0,
        match_cost: int = 1,
        symmetric: bool = True,
        external: bool = True,
    ) -> None:
        self.mat = mat
        self.mismatch_cost = mismatch_cost
        self.match_cost = match_cost
        self.symmetric = symmetric

    def maximum(self, *sequences: Sequence) -> int:
        return self.match_cost

    def __call__(self, *sequences: Sequence) -> int:
        if not self.mat:
            if self._ident(*sequences):
                return self.match_cost
            return self.mismatch_cost

        # search in matrix
        if sequences in self.mat:
            return self.mat[sequences]
        # search in symmetric matrix
        if self.symmetric:
            sequences = tuple(reversed(sequences))
            if sequences in self.mat:
                return self.mat[sequences]
        # if identity then return match_cost
        if self._ident(*sequences):
            return self.match_cost
        # not found
        return self.mismatch_cost


prefix = Prefix()
postfix = Postfix()
length = Length()
identity = Identity()
matrix = Matrix()
