# coding=utf-8

from app import socketio


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


def show_message(msg):
    event_stream(type="message", payload=msg)


def show_progress(id, header, name, value, count):
    event_stream(type="progress", payload={"id": id, "header": header, "name": name, "value": value, "count": count})


def hide_progress(id):
    event_stream(type="progress", action="delete", payload=id)
