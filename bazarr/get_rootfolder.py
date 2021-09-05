# coding=utf-8

from database import TableShowsRootfolder, TableMoviesRootfolder

def get_series_rootfolder():
    rootfolders = TableShowsRootfolder.select().dicts()


def get_movies_rootfolder():
    rootfolders = TableMoviesRootfolder.select().dicts()


def check_series_rootfolder():
    pass


def check_movies_rootfolder():
    pass
