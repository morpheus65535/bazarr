from sqlalchemy import select

def test_movie_row_factory_inserts_rows(
    movie_row_factory,
    transactional_session,
    wanted_search_tables,
):
    movie = movie_row_factory(radarrId=42, title="In Bruges")

    row = transactional_session.execute(
        select(wanted_search_tables.movie.c.radarrId, wanted_search_tables.movie.c.title).where(
            wanted_search_tables.movie.c.radarrId == 42
        )
    ).one()

    assert movie.radarrId == 42
    assert row == (42, "In Bruges")


def test_series_row_factories_insert_related_rows(
    show_row_factory,
    episode_row_factory,
    transactional_session,
    wanted_search_tables,
):
    show = show_row_factory(sonarrSeriesId=99, title="Black Books")
    episode = episode_row_factory(sonarrSeriesId=show.sonarrSeriesId, sonarrEpisodeId=501)

    show_row = transactional_session.execute(
        select(wanted_search_tables.show.c.sonarrSeriesId, wanted_search_tables.show.c.title).where(
            wanted_search_tables.show.c.sonarrSeriesId == 99
        )
    ).one()
    episode_row = transactional_session.execute(
        select(
            wanted_search_tables.episode.c.sonarrEpisodeId,
            wanted_search_tables.episode.c.sonarrSeriesId,
        ).where(
            wanted_search_tables.episode.c.sonarrEpisodeId == 501
        )
    ).one()

    assert show_row == (99, "Black Books")
    assert episode_row == (501, 99)
    assert episode.sonarrSeriesId == show.sonarrSeriesId
