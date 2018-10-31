import time

from wraptor.context import throttle

def test_basic():
    arr = []
    t = throttle(.1)

    with t:
        arr.append(1)
    with t:
        arr.append(1)
    time.sleep(.2)
    with t:
        arr.append(1)

    assert arr == [1, 1]
