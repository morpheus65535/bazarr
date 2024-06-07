from __future__ import annotations

# built-in
from itertools import permutations, product
from typing import Sequence


__all__ = ['words_combinations', 'find_ngrams']


def words_combinations(f, *texts) -> float:
    m = float('Inf')
    # split by words
    texts = [t.split() for t in texts]
    # permutations
    texts = [permutations(words) for words in texts]
    # combinations
    for subtexts in product(*texts):
        if f.equality:
            words_min_cnt = len(min(subtexts, key=len))
            subtexts = [t[:words_min_cnt] for t in subtexts]
        subtexts = [' '.join(t) for t in subtexts]
        m = min(m, f(*subtexts))
    return m


def find_ngrams(input_list: Sequence, n: int) -> list[tuple]:
    return list(zip(*[input_list[i:] for i in range(n)]))
