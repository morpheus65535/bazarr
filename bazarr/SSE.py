from __future__ import absolute_import
from collections import deque
import json
import time


class EventStream:
    """
    This class is used to read or write items to the notifications deque.
    """
    
    def __init__(self):
        self.queue = deque(maxlen=100)
    
    def write(self, type=None, series=None, episode=None, movie=None):
        """
            :param type: The type of element.
            :type type: str
            :param type: The series id.
            :type type: str
            :param type: The episode id.
            :type type: str
            :param type: The movie id.
            :type type: str
        """
        msg = {"type": type, "series": series, "episode": episode, "movie": movie}
        self.queue.append("data:" + json.dumps(msg) + "\n\n")
    
    def read(self):
        """
            :return: Return the oldest notification available.
            :rtype: str
        """

        while True:
            if self.queue:
                return self.queue.popleft()
            else:
                return ':'
            time.sleep(0.1)


event_stream = EventStream()
