import time
from wraptor.context import maybe

class throttle(maybe):
    def __init__(self, seconds=1):
        self.seconds = seconds
        self.last_run = 0

        def predicate():
            now = time.time()
            if now > self.last_run + self.seconds:
                self.last_run = now
                return True
            return False

        maybe.__init__(self, predicate)
