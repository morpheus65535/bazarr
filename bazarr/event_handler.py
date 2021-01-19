# coding=utf-8

import json
from app import socketio


def event_stream(type=None, action=None, series=None, episode=None, movie=None, task=None):
    """
        :param type: The type of element.
        :type type: str
        :param action: The action type of element from insert, update, delete.
        :type action: str
        :param series: The series id.
        :type series: str
        :param episode: The episode id.
        :type episode: str
        :param movie: The movie id.
        :type movie: str
        :param task: The task id.
        :type task: str
    """
    socketio.emit('event', json.dumps({"type": type, "action": action, "series": series, "episode": episode,
                                       "movie": movie, "task": task}))
