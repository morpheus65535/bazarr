import doctest
import logging
import math
import os
import unittest
from contextlib import contextmanager
from logging.handlers import BufferingHandler

from pint import Quantity, UnitRegistry, logger
from pint.compat import ndarray, np
from pint.testsuite.helpers import PintOutputChecker


class TestHandler(BufferingHandler):
    def __init__(self, only_warnings=False):
        # BufferingHandler takes a "capacity" argument
        # so as to know when to flush. As we're overriding
        # shouldFlush anyway, we can set a capacity of zero.
        # You can call flush() manually to clear out the
        # buffer.
        self.only_warnings = only_warnings
        BufferingHandler.__init__(self, 0)

    def shouldFlush(self):
        return False

    def emit(self, record):
        if self.only_warnings and record.level != logging.WARNING:
            return
        self.buffer.append(record.__dict__)


class BaseTestCase(unittest.TestCase):

    CHECK_NO_WARNING = True

    @contextmanager
    def capture_log(self, level=logging.DEBUG):
        th = TestHandler()
        th.setLevel(level)
        logger.addHandler(th)
        if self._test_handler is not None:
            buflen = len(self._test_handler.buffer)
        yield th.buffer
        if self._test_handler is not None:
            self._test_handler.buffer = self._test_handler.buffer[:buflen]

    def setUp(self):
        self._test_handler = None
        if self.CHECK_NO_WARNING:
            self._test_handler = th = TestHandler()
            th.setLevel(logging.WARNING)
            logger.addHandler(th)

    def tearDown(self):
        if self._test_handler is not None:
            buf = self._test_handler.buffer
            msg = "\n".join(record.get("msg", str(record)) for record in buf)
            self.assertEqual(len(buf), 0, msg=f"{len(buf)} warnings raised.\n{msg}")


class QuantityTestCase(BaseTestCase):

    FORCE_NDARRAY = False

    @classmethod
    def setUpClass(cls):
        cls.ureg = UnitRegistry(force_ndarray=cls.FORCE_NDARRAY)
        cls.Q_ = cls.ureg.Quantity
        cls.U_ = cls.ureg.Unit

    def _get_comparable_magnitudes(self, first, second, msg):
        if isinstance(first, Quantity) and isinstance(second, Quantity):
            second = second.to(first)
            self.assertEqual(
                first.units, second.units, msg=msg + " Units are not equal."
            )
            m1, m2 = first.magnitude, second.magnitude
        elif isinstance(first, Quantity):
            self.assertTrue(
                first.dimensionless, msg=msg + " The first is not dimensionless."
            )
            first = first.to("")
            m1, m2 = first.magnitude, second
        elif isinstance(second, Quantity):
            self.assertTrue(
                second.dimensionless, msg=msg + " The second is not dimensionless."
            )
            second = second.to("")
            m1, m2 = first, second.magnitude
        else:
            m1, m2 = first, second

        return m1, m2

    def assertQuantityEqual(self, first, second, msg=None):
        if msg is None:
            msg = "Comparing %r and %r. " % (first, second)

        m1, m2 = self._get_comparable_magnitudes(first, second, msg)

        if isinstance(m1, ndarray) or isinstance(m2, ndarray):
            np.testing.assert_array_equal(m1, m2, err_msg=msg)
        elif math.isnan(m1):
            self.assertTrue(math.isnan(m2), msg)
        elif math.isnan(m2):
            self.assertTrue(math.isnan(m1), msg)
        else:
            self.assertEqual(m1, m2, msg)

    def assertQuantityAlmostEqual(self, first, second, rtol=1e-07, atol=0, msg=None):
        if msg is None:
            try:
                msg = "Comparing %r and %r. " % (first, second)
            except TypeError:
                try:
                    msg = "Comparing %s and %s. " % (first, second)
                except Exception:
                    msg = "Comparing"

        m1, m2 = self._get_comparable_magnitudes(first, second, msg)

        if isinstance(m1, ndarray) or isinstance(m2, ndarray):
            np.testing.assert_allclose(m1, m2, rtol=rtol, atol=atol, err_msg=msg)
        elif math.isnan(m1):
            self.assertTrue(math.isnan(m2), msg)
        elif math.isnan(m2):
            self.assertTrue(math.isnan(m1), msg)
        else:
            self.assertLessEqual(abs(m1 - m2), atol + rtol * abs(m2), msg=msg)


class CaseInsensitveQuantityTestCase(QuantityTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ureg = UnitRegistry(case_sensitive=False)
        cls.Q_ = cls.ureg.Quantity
        cls.U_ = cls.ureg.Unit


def testsuite():
    """A testsuite that has all the pint tests."""
    suite = unittest.TestLoader().discover(os.path.dirname(__file__))
    from pint.compat import HAS_NUMPY, HAS_UNCERTAINTIES

    # TESTING THE DOCUMENTATION requires pyyaml, serialize, numpy and uncertainties
    if HAS_NUMPY and HAS_UNCERTAINTIES:
        try:
            import serialize  # noqa: F401
            import yaml  # noqa: F401

            add_docs(suite)
        except ImportError:
            pass
    return suite


def main():
    """Runs the testsuite as command line application."""
    try:
        unittest.main()
    except Exception as e:
        print("Error: %s" % e)


def run():
    """Run all tests.

    :return: a :class:`unittest.TestResult` object

    Parameters
    ----------

    Returns
    -------

    """
    test_runner = unittest.TextTestRunner()
    return test_runner.run(testsuite())


_GLOBS = {
    "wrapping.rst": {
        "pendulum_period": lambda length: 2 * math.pi * math.sqrt(length / 9.806650),
        "pendulum_period2": lambda length, swing_amplitude: 1.0,
        "pendulum_period_maxspeed": lambda length, swing_amplitude: (1.0, 2.0),
        "pendulum_period_error": lambda length: (1.0, False),
    }
}


def add_docs(suite):
    """Add docs to suite

    Parameters
    ----------
    suite :


    Returns
    -------

    """
    docpath = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
    docpath = os.path.abspath(docpath)
    if os.path.exists(docpath):
        checker = PintOutputChecker()
        for name in (name for name in os.listdir(docpath) if name.endswith(".rst")):
            file = os.path.join(docpath, name)
            suite.addTest(
                doctest.DocFileSuite(
                    file,
                    module_relative=False,
                    checker=checker,
                    globs=_GLOBS.get(name, None),
                )
            )


def test_docs():
    suite = unittest.TestSuite()
    add_docs(suite)
    runner = unittest.TextTestRunner()
    return runner.run(suite)
