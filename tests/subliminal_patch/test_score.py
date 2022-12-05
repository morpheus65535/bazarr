from subliminal_patch import score
from subliminal_patch.providers.karagarga import KaragargaSubtitle


# def __call__(self, matches, subtitle, video, hearing_impaired=None):


def test_compute_score_set_var(movies, languages):
    subtitle = KaragargaSubtitle(languages["en"], "", "", "")
    score.compute_score({"hash"}, subtitle, movies["dune"])


def test_compute_score_set_var_w_episode(episodes, languages):
    subtitle = KaragargaSubtitle(languages["en"], "", "", "")
    score.compute_score({"hash"}, subtitle, episodes["breaking_bad_s01e01"])


def test_compute_score_defaults():
    assert score.ComputeScore()._scores == score.DEFAULT_SCORES


def test_compute_score_custom_invalid():
    assert (
        score.ComputeScore({"movie": {"hash": 120}, "episode": {"hash": 321}})._scores
        == score.DEFAULT_SCORES
    )


def test_compute_score_custom_valid():
    scores_copy = score.DEFAULT_SCORES.copy()
    scores_copy["movie"]["release_group"] = 12
    scores_copy["movie"]["source"] = 8

    scores_ = score.ComputeScore(scores_copy)
    assert scores_._scores["movie"]["release_group"] == 12
    assert scores_._scores["movie"]["source"] == 8
