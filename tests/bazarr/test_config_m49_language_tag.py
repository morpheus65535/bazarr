# -*- coding: utf-8 -*-
from app.config import settings


def test_use_m49_language_tag_defaults_to_disabled() -> None:
    assert settings.general.use_m49_language_tag is False
