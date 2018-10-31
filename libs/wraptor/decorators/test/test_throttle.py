import time

from wraptor.decorators import throttle

def test_basic():
    arr = []

    @throttle(.1)
    def test():
        arr.append(1)

    test()
    test()
    time.sleep(.2)
    test()

    assert arr == [1, 1]

def test_fail_instance_method():
    """ Test that throttle without instance_method creates a globally
        shared throttle instance (shared by all instances of the class)
    """
    arr = []

    class foo(object):
        @throttle(1)
        def bar(self):
            arr.append(1)

    x = foo()
    x2 = foo()

    x.bar()
    x2.bar()
    # throttle
    assert arr == [1]

def test_class_method():
    arr = []

    class foo(object):
        @throttle(1, instance_method=True)
        def bar(self):
            arr.append(1)

    x = foo()
    x2 = foo()

    x.bar()
    x2.bar()
    assert arr == [1, 1]
