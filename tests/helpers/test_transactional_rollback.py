from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import select
from sqlalchemy import text


metadata = MetaData()
widgets = Table(
    "widgets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)


def test_transactional_session_insert_exercise_assert(transactional_engine, transactional_session):
    metadata.create_all(transactional_engine)

    transactional_session.execute(widgets.insert().values(id=1, name="alpha"))
    transactional_session.flush()

    row = transactional_session.execute(select(widgets.c.name).where(widgets.c.id == 1)).scalar_one()
    assert row == "alpha"


def test_transactional_session_rolls_back_between_tests(transactional_engine, transactional_session):
    metadata.create_all(transactional_engine)

    count = transactional_session.execute(text("SELECT COUNT(*) FROM widgets")).scalar_one()
    assert count == 0
