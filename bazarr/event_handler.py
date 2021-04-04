# coding=utf-8

import json
from app import socketio


def event_stream(type, action: str = "update", id=None):
    """
        :param type: The type of element.
        :type type: str
        :param action: The action type of element from insert, update, delete.
        :type action: str
        :param id: The id of element, None means all.
    """

    try:
        if id is not None:
            id = int(id)
        socketio.emit(type, {"action": action, "id": id})
    except:
        # TODO
        pass
