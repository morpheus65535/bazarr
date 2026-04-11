import logging

from typing import Callable
from ..helpers import Helpers
class StreamHandler(object):
    def __init__(self, event: str, invocation_id: str):
        self.event = event
        self.invocation_id = invocation_id
        self.logger = Helpers.get_logger()
        self.next_callback =\
            lambda _: self.logger.warning(
                "next stream handler fired, no callback configured")
        self.complete_callback =\
            lambda _: self.logger.warning(
                "next complete handler fired, no callback configured")
        self.error_callback =\
            lambda _: self.logger.warning(
                "next error handler fired, no callback configured")

    def subscribe(self, subscribe_callbacks: dict):
        error =\
            " subscribe object must be a dict like {0}"\
            .format({
                "next": None,
                "complete": None,
                "error": None
                })

        if subscribe_callbacks is None or\
                type(subscribe_callbacks) is not dict:
            raise TypeError(error)

        if "next" not in subscribe_callbacks or\
                "complete" not in subscribe_callbacks \
                or "error" not in subscribe_callbacks:
            raise KeyError(error)

        if not callable(subscribe_callbacks["next"])\
                or not callable(subscribe_callbacks["next"]) \
                or not callable(subscribe_callbacks["next"]):
            raise ValueError("Suscribe callbacks must be functions")

        self.next_callback = subscribe_callbacks["next"]
        self.complete_callback = subscribe_callbacks["complete"]
        self.error_callback = subscribe_callbacks["error"]


class InvocationHandler(object):
    def __init__(self, invocation_id: str, complete_callback: Callable):
        self.invocation_id = invocation_id
        self.complete_callback = complete_callback
