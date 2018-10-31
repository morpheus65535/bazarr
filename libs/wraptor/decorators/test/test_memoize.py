import time

from wraptor.decorators import memoize

def test_basic_noargs():
    arr = []

    @memoize()
    def fn():
        arr.append(1)

    fn()
    fn()

    assert arr == [1]

def test_basic_args():
    arr = []

    @memoize()
    def fn(*args, **kwargs):
        arr.append(1)

    s_args = [1, 2, 3]
    fn(*s_args)
    fn(*s_args)
    c_args = [[1], "asdjf", {'a': 5}]
    fn(*c_args)
    fn(*c_args)
    kw_args = {'a': 234, 'b': [1, 2, "asdf"], 'c': [5, 6]}
    kw_args_2 = {'a': 234, 'b': [1, 3, "asdf"], 'c': [5, 6]}
    fn(*c_args, **kw_args)
    fn(*c_args, **kw_args_2)
    fn(*c_args, **kw_args)

    fn(fn)
    fn(fn)

    assert arr == [1, 1, 1, 1, 1]

def test_timeout():
    arr = []

    @memoize(timeout=.1)
    def fn(*args, **kwargs):
        arr.append(1)

    fn(1, 2, 3)
    time.sleep(.2)
    fn(1, 2, 3)

    assert arr == [1, 1]

def test_auto_flush():
    memoize_inst = memoize(timeout=.1)

    @memoize_inst
    def fn(*args, **kwargs):
        pass

    fn(1, 2, 3)
    assert len(memoize_inst.cache.keys()) == 1
    time.sleep(.2)
    fn(1, 2, 3)
    assert len(memoize_inst.cache.keys()) == 1

def test_manual_flush():
    memoize_inst = memoize(timeout=.1, manual_flush=True)

    @memoize_inst
    def fn(*args, **kwargs):
        pass

    fn(1, 2, 3)
    assert len(memoize_inst.cache.keys()) == 1
    time.sleep(.2)
    fn(3, 4, 5)
    assert len(memoize_inst.cache.keys()) == 2
    time.sleep(.2)
    fn.flush_cache()
    assert len(memoize_inst.cache.keys()) == 0

def test_class_method():
    import random

    memoizer = memoize(manual_flush=True, instance_method=True)

    class foo(object):
        @memoizer
        def bar(self, *args):
            return random.random()

    x = foo()
    x2 = foo()

    assert x.bar('a', 'b') != x2.bar('a', 'b')
    assert x.bar('a', 'b') == x.bar('a', 'b')
    assert x.bar('a', 'b') != x.bar('a', 'd')
    assert x2.bar('a', 'b') == x2.bar('a', 'b')

    # the memoizer should have made private caches for each instance
    assert len(memoizer.cache) == 0

    # now make sure that they don't share caches
    res1 = x.bar('a', 'b')
    res2 = x2.bar('a', 'b')
    x.bar.flush_cache()
    assert res1 != x.bar('a', 'b')
    assert res2 == x2.bar('a', 'b')

def test_instance_method_extended():

    class foo(object):
        def __init__(self):
            self.i = 0

        @memoize(instance_method=True)
        def bar(self, instance):
            assert self == instance
            self.i += 1
            return self.i

    f = foo()
    assert f.bar(f) == 1
    assert f.bar(f) == 1

def test_fail_instance_method():
    """ Test that memoize without instance_method creates a globally
        shared memoize instance (shared by all instances of the class)
    """
    memoizer = memoize(manual_flush=True)

    class foo(object):
        def __init__(self, x):
            self._x = x

        @memoizer
        def bar(self):
            return self._x

    x = foo(1)
    x2 = foo(2)

    assert x.bar() != x2.bar()

    # note that they share the same cache
    assert len(memoizer.cache) == 2
