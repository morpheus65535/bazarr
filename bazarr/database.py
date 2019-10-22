import os
from sqlite3worker import Sqlite3Worker

from get_args import args
from helper import path_replace, path_replace_movie, path_replace_reverse, path_replace_reverse_movie

database = Sqlite3Worker(os.path.join(args.config_dir, 'db', 'bazarr.db'), max_queue_size=256)
