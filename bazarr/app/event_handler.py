# coding=utf-8

from .app import socketio


def event_stream(type, action="update", payload=None):
    """
        :param type: The type of element.
        :type type: str
        :param action: The action type of element from update and delete.
        :type action: str
        :param payload: The payload to send, can be anything
    """

    try:
        payload = int(payload)
    except (ValueError, TypeError):
        pass
    socketio.emit("data", {"type": type, "action": action, "payload": payload})
