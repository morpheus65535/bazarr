from uuid import uuid4

import pytest


@pytest.mark.parametrize('tag', ["O'Brien", r'A\B', '100% Safe', 'ufc'])
def test_sportarr_tag_exclusion_matches_the_exact_label(monkeypatch, tag):
    from app.config import settings
    from app.database import (TableSportsLeagues, database, delete,
                              get_exclusion_clause, insert, select)

    token = uuid4().hex[:8]
    ids = [int(token, 16) + offset for offset in range(3)]
    monkeypatch.setattr(settings.sportarr, 'excluded_tags', [tag])
    monkeypatch.setattr(settings.sportarr, 'excluded_sports', [])
    monkeypatch.setattr(settings.sportarr, 'only_monitored', False)

    try:
        database.execute(insert(TableSportsLeagues).values(
            sportarrLeagueId=ids[0], title='Excluded', path=f'/tmp/bazarr-pr3524-{token}-excluded', tags=str([tag])))
        database.execute(insert(TableSportsLeagues).values(
            sportarrLeagueId=ids[1], title='Allowed', path=f'/tmp/bazarr-pr3524-{token}-allowed',
            tags=str([tag + ' Extra'])))
        database.execute(insert(TableSportsLeagues).values(
            sportarrLeagueId=ids[2], title='Different case', path=f'/tmp/bazarr-pr3524-{token}-case',
            tags=str([tag.swapcase()])))

        found = database.execute(
            select(TableSportsLeagues.sportarrLeagueId)
            .where(TableSportsLeagues.sportarrLeagueId.in_(ids))
            .where(*get_exclusion_clause('sports'))).scalars().all()

        assert found == ids[1:]
    finally:
        database.execute(delete(TableSportsLeagues).where(TableSportsLeagues.sportarrLeagueId.in_(ids)))
        database.commit()
