import logging
import os

import pytest
from peewee import SqliteDatabase

os.environ["NO_CLI"] = "true"
os.environ["SZ_USER_AGENT"] = "test"

logging.getLogger("rebulk").setLevel(logging.WARNING)

test_db = SqliteDatabase(':memory:')


@pytest.fixture()
def app():
    from app.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture(scope="module")
def db():
    from app.database import TableEpisodes, TableShows
    MODELS = [TableEpisodes, TableShows]
    test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(MODELS)
    yield
    test_db.drop_tables(MODELS)
    test_db.close()
