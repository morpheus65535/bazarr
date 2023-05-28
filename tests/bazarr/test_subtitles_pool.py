from bazarr.subtitles import pool


def test_init_pool():
    assert pool._init_pool("movie")


def test_pool_update():
    pool_ = pool._init_pool("movie")
    assert pool._pool_update(pool_, "movie")
