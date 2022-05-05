# -*- coding: utf-8 -*-

from guessit import guessit


def convert_to_guessit(guessit_key, attr_from_db):
    try:
        return guessit(attr_from_db)[guessit_key]
    except KeyError:
        return attr_from_db
