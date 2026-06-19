import importlib


migration = importlib.import_module("migrations.versions.e6cbb0f6f9b1_")


def test_migration_appends_missing_rows_using_shared_text_parser():
    rows = []

    migration._append_missing_rows("movie", 7, "['en', None, 'fr:hi', 'en']", rows)

    assert rows == [("movie", 7, "en"), ("movie", 7, "fr:hi")]


def test_migration_appends_attempt_rows_using_shared_attempt_parser():
    rows = []

    migration._append_attempt_rows("series", 17, "[['en', 1], ['en', 3], ['fr', 2]]", rows)

    assert rows == [
        ("series", 17, "en", 1.0, 3.0),
        ("series", 17, "fr", 2.0, 2.0),
    ]
