import pytest
from sqlalchemy import Text, create_engine, literal, select
from sqlalchemy.orm import Session

from app.database import TableShows, text_boolean
from sonarr.sync import series


@pytest.mark.parametrize(('stored', 'expected'), [
    ('True', True), ('true', True), ('False', False), ('false', False),
    ('TRUE', None), ('FALSE', None), ('tRuE', None), (' false ', None),
    (None, None), ('', None), ('0', None), ('1', None), ('yes', None),
])
def test_monitored_text_is_decoded_before_the_sync_loop(stored: str | None, expected: bool | None) -> None:
    engine = create_engine('sqlite://')
    try:
        with engine.connect() as connection:
            actual = connection.execute(select(text_boolean(literal(stored, type_=Text)))).scalar_one()
        assert actual is expected
    finally:
        engine.dispose()


def test_series_monitored_lookup_only_retains_known_flags(
    memory_session: Session, monkeypatch: pytest.MonkeyPatch,
) -> None:
    stored = ['True', 'true', 'False', 'false', 'TRUE', 'FALSE', '', '0', 'yes', None]
    for identifier, value in enumerate(stored, start=1):
        memory_session.add(TableShows(sonarrSeriesId=identifier, path=f'/show/{identifier}',
                                     title='Show', monitored=value))
    memory_session.flush()
    monkeypatch.setattr(series, 'database', memory_session)
    assert series.get_series_monitored_table() == {1: True, 2: True, 3: False, 4: False}
