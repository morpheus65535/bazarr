from collections import deque
import json


class Notify:
    """
    This class is used to read or write items to the notifications deque.
    """
    
    def __init__(self):
        self.queue = deque(maxlen=10)
    
    def write(self, msg, type='info', duration='temporary', button='null', queue='main', item=0, length=0):
        """
            :param msg: The message to display.
            :type msg: str
            :param type: The type of notification that can be: alert, success, error, warning, info
            :type type: str
            :param duration: The duration of the notification that can be: temporary, permanent
            :type duration: str
            :param button: The kind of button desired that can be: null, refresh, restart
            :type button: str
            :param queue: The name of the notification queue to use. Default is 'main'
            :type duration: str
            :param item: The number of the item for progress bar
            :type item: int
            :param length: The length of the group of item for progress bar
            :type length: int
        """
        
        self.queue.append(json.dumps([msg, type, duration, button, queue, item, length]))
    
    def read(self):
        """
            :return: Return the oldest notification available.
            :rtype: str
        """
        
        if self.queue:
            return self.queue.popleft()


notifications = Notify()
