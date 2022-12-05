from subliminal_patch import subtitle


def test_guess_matches_w_edition_only_video(movies):
    movie = movies["dune"]
    movie.edition = "Director's Cut"
    matches = subtitle.guess_matches(movie, {})
    assert "edition" not in matches


def test_guess_matches_w_edition_only_guess(movies):
    movie = movies["dune"]
    movie.edition = None
    matches = subtitle.guess_matches(movie, {"edition": "Director's Cut"})
    assert "edition" not in matches


def test_guess_matches_w_edition_both(movies):
    movie = movies["dune"]
    movie.edition = "Director's Cut"
    matches = subtitle.guess_matches(movie, {"edition": "Director's Cut"})
    assert "edition" in matches


def test_guess_matches_w_edition_both_empty(movies):
    movie = movies["dune"]
    movie.edition = None
    matches = subtitle.guess_matches(movie, {})
    assert "edition" in matches
