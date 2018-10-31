# coding=utf-8

import sys
from itertools import chain, combinations, permutations

from subliminal.video import Episode


def permute(x):
    return [base_score + i + j for i in x for j in x]

if __name__ == "__main__":
    scores = Episode.scores
    base_score_keys = ["series", "season", "episode"]
    leftover_keys = list(set(scores.keys()) - set(base_score_keys))
    base_score = sum([val for key, val in scores.items() if key in base_score_keys])
    leftover_scores = set([score for key, score in scores.items() if key in leftover_keys])
    print "base score:", base_score
    print "leftover:", sorted(set(leftover_scores))
    # print sum_possible_scores(base_score, leftover_scores)
    # print list(permutations(leftover_scores))
    print ",\n".join(map(lambda x: '"%s"' % x, ["66"] + sorted(set(permute(leftover_scores)))))
