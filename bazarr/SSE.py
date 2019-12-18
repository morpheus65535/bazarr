from __future__ import absolute_import
from collections import deque
import json
import time


class EventStream:
    """
    This class is used to read or write items to the notifications deque.
    """
    
    def __init__(self):
        self.queue = deque(maxlen=10)
    
    def write(self, msg):
        """
            :param msg: The message to display.
            :type msg: str
        """
        
        self.queue.append("data:" + msg + "\n\n")
    
    def read(self):
        """
            :return: Return the oldest notification available.
            :rtype: str
        """

        if self.queue or (len(self.queue) > 0):
            return self.queue.popleft()


event_stream = EventStream()
