from pint import DimensionalityError
from pint.compat import np
from pint.testsuite import QuantityTestCase, helpers

# Following http://docs.scipy.org/doc/numpy/reference/ufuncs.html

if np:
    pi = np.pi


@helpers.requires_numpy()
class TestUFuncs(QuantityTestCase):

    FORCE_NDARRAY = True

    @property
    def qless(self):
        return np.asarray([1.0, 2.0, 3.0, 4.0]) * self.ureg.dimensionless

    @property
    def qs(self):
        return 8 * self.ureg.J

    @property
    def q1(self):
        return np.asarray([1.0, 2.0, 3.0, 4.0]) * self.ureg.J

    @property
    def q2(self):
        return 2 * self.q1

    @property
    def qm(self):
        return np.asarray([1.0, 2.0, 3.0, 4.0]) * self.ureg.m

    @property
    def qi(self):
        return np.asarray([1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j]) * self.ureg.m

    def _test1(
        self, func, ok_with, raise_with=(), output_units="same", results=None, rtol=1e-6
    ):
        """Test function that takes a single argument and returns Quantity.

        Parameters
        ----------
        func :
            function callable.
        ok_with :
            iterables of values that work fine.
        raise_with :
            iterables of values that raise exceptions. (Default value = ())
        output_units :
            units to be used when building results.
            'same': ok_with[n].units (default).
            is float: ok_with[n].units ** output_units.
            None: no output units, the result should be an ndarray.
            Other value will be parsed as unit.
        results :
            iterable of results.
            If None, the result will be obtained by applying
            func to each ok_with value (Default value = None)
        rtol :
            relative tolerance. (Default value = 1e-6)

        Returns
        -------

        """
        if results is None:
            results = [None] * len(ok_with)
        for x1, res in zip(ok_with, results):
            err_msg = "At {} with {}".format(func.__name__, x1)
            if output_units == "same":
                ou = x1.units
            elif isinstance(output_units, (int, float)):
                ou = x1.units ** output_units
            else:
                ou = output_units

            qm = func(x1)
            if res is None:
                res = func(x1.magnitude)
                if ou is not None:
                    res = self.Q_(res, ou)

            self.assertQuantityAlmostEqual(qm, res, rtol=rtol, msg=err_msg)

        for x1 in raise_with:
            with self.assertRaises(
                DimensionalityError, msg=f"At {func.__name__} with {x1}"
            ):
                func(x1)

    def _testn(self, func, ok_with, raise_with=(), results=None):
        """Test function that takes a single argument and returns and ndarray (not a Quantity)

        Parameters
        ----------
        func :
            function callable.
        ok_with :
            iterables of values that work fine.
        raise_with :
            iterables of values that raise exceptions. (Default value = ())
        results :
            iterable of results.
            If None, the result will be obtained by applying
            func to each ok_with value (Default value = None)

        Returns
        -------

        """
        self._test1(func, ok_with, raise_with, output_units=None, results=results)

    def _test1_2o(
        self,
        func,
        ok_with,
        raise_with=(),
        output_units=("same", "same"),
        results=None,
        rtol=1e-6,
    ):
        """Test functions that takes a single argument and return two Quantities.

        Parameters
        ----------
        func :
            function callable.
        ok_with :
            iterables of values that work fine.
        raise_with :
            iterables of values that raise exceptions. (Default value = ())
        output_units :
            tuple of units to be used when building the result tuple.
            'same': ok_with[n].units (default).
            is float: ok_with[n].units ** output_units.
            None: no output units, the result should be an ndarray.
            Other value will be parsed as unit.
        results :
            iterable of results.
            If None, the result will be obtained by applying
            func to each ok_with value (Default value = None)
        rtol :
            relative tolerance. (Default value = 1e-6)
        "same") :


        Returns
        -------

        """

        if results is None:
            results = [None] * len(ok_with)
        for x1, res in zip(ok_with, results):
            err_msg = "At {} with {}".format(func.__name__, x1)
            qms = func(x1)
            if res is None:
                res = func(x1.magnitude)

            for ndx, (qm, re, ou) in enumerate(zip(qms, res, output_units)):
                if ou == "same":
                    ou = x1.units
                elif isinstance(ou, (int, float)):
                    ou = x1.units ** ou

                if ou is not None:
                    re = self.Q_(re, ou)

                self.assertQuantityAlmostEqual(qm, re, rtol=rtol, msg=err_msg)

        for x1 in raise_with:
            with self.assertRaises(ValueError, msg=f"At {func.__name__} with {x1}"):
                func(x1)

    def _test2(
        self,
        func,
        x1,
        ok_with,
        raise_with=(),
        output_units="same",
        rtol=1e-6,
        convert2=True,
    ):
        """Test function that takes two arguments and return a Quantity.

        Parameters
        ----------
        func :
            function callable.
        x1 :
            first argument of func.
        ok_with :
            iterables of values that work fine.
        raise_with :
            iterables of values that raise exceptions. (Default value = ())
        output_units :
            units to be used when building results.
            'same': x1.units (default).
            'prod': x1.units * ok_with[n].units
            'div': x1.units / ok_with[n].units
            'second': x1.units * ok_with[n]
            None: no output units, the result should be an ndarray.
            Other value will be parsed as unit.
        rtol :
            relative tolerance. (Default value = 1e-6)
        convert2 :
            if the ok_with[n] should be converted to x1.units. (Default value = True)

        Returns
        -------

        """
        for x2 in ok_with:
            err_msg = "At {} with {} and {}".format(func.__name__, x1, x2)
            if output_units == "same":
                ou = x1.units
            elif output_units == "prod":
                ou = x1.units * x2.units
            elif output_units == "div":
                ou = x1.units / x2.units
            elif output_units == "second":
                ou = x1.units ** x2
            else:
                ou = output_units

            qm = func(x1, x2)

            if convert2 and hasattr(x2, "magnitude"):
                m2 = x2.to(getattr(x1, "units", "")).magnitude
            else:
                m2 = getattr(x2, "magnitude", x2)

            res = func(x1.magnitude, m2)
            if ou is not None:
                res = self.Q_(res, ou)

            self.assertQuantityAlmostEqual(qm, res, rtol=rtol, msg=err_msg)

        for x2 in raise_with:
            with self.assertRaises(
                DimensionalityError, msg=f"At {func.__name__} with {x1} and {x2}"
            ):
                func(x1, x2)

    def _testn2(self, func, x1, ok_with, raise_with=()):
        """Test function that takes two arguments and return a ndarray.

        Parameters
        ----------
        func :
            function callable.
        x1 :
            first argument of func.
        ok_with :
            iterables of values that work fine.
        raise_with :
            iterables of values that raise exceptions. (Default value = ())

        Returns
        -------

        """
        self._test2(func, x1, ok_with, raise_with, output_units=None)


@helpers.requires_numpy()
class TestMathUfuncs(TestUFuncs):
    """Universal functions (ufunc) > Math operations

    http://docs.scipy.org/doc/numpy/reference/ufuncs.html#math-operations

    add(x1, x2[, out]) 	Add arguments element-wise.
    subtract(x1, x2[, out]) 	Subtract arguments, element-wise.
    multiply(x1, x2[, out]) 	Multiply arguments element-wise.
    divide(x1, x2[, out]) 	Divide arguments element-wise.
    logaddexp(x1, x2[, out]) 	Logarithm of the sum of exponentiations of the inputs.
    logaddexp2(x1, x2[, out]) 	Logarithm of the sum of exponentiations of the inputs in base-2.
    true_divide(x1, x2[, out]) 	Returns a true division of the inputs, element-wise.
    floor_divide(x1, x2[, out]) 	Return the largest integer smaller or equal to the division of the inputs.
    negative(x[, out]) 	Returns an array with the negative of each element of the original array.
    power(x1, x2[, out]) 	First array elements raised to powers from second array, element-wise. NOT IMPLEMENTED
    remainder(x1, x2[, out]) 	Return element-wise remainder of division.
    mod(x1, x2[, out]) 	Return element-wise remainder of division.
    fmod(x1, x2[, out]) 	Return the element-wise remainder of division.
    absolute(x[, out]) 	Calculate the absolute value element-wise.
    rint(x[, out]) 	Round elements of the array to the nearest integer.
    sign(x[, out]) 	Returns an element-wise indication of the sign of a number.
    conj(x[, out]) 	Return the complex conjugate, element-wise.
    exp(x[, out]) 	Calculate the exponential of all elements in the input array.
    exp2(x[, out]) 	Calculate 2**p for all p in the input array.
    log(x[, out]) 	Natural logarithm, element-wise.
    log2(x[, out]) 	Base-2 logarithm of x.
    log10(x[, out]) 	Return the base 10 logarithm of the input array, element-wise.
    expm1(x[, out]) 	Calculate exp(x) - 1 for all elements in the array.
    log1p(x[, out]) 	Return the natural logarithm of one plus the input array, element-wise.
    sqrt(x[, out]) 	Return the positive square-root of an array, element-wise.
    square(x[, out]) 	Return the element-wise square of the input.
    reciprocal(x[, out]) 	Return the reciprocal of the argument, element-wise.
    ones_like(x[, out]) 	Returns an array of ones with the same shape and type as a given array.

    Parameters
    ----------

    Returns
    -------

    """

    def test_add(self):
        self._test2(np.add, self.q1, (self.q2, self.qs), (self.qm,))

    def test_subtract(self):
        self._test2(np.subtract, self.q1, (self.q2, self.qs), (self.qm,))

    def test_multiply(self):
        self._test2(np.multiply, self.q1, (self.q2, self.qs), (), "prod")

    def test_divide(self):
        self._test2(
            np.divide,
            self.q1,
            (self.q2, self.qs, self.qless),
            (),
            "div",
            convert2=False,
        )

    def test_logaddexp(self):
        self._test2(np.logaddexp, self.qless, (self.qless,), (self.q1,), "")

    def test_logaddexp2(self):
        self._test2(np.logaddexp2, self.qless, (self.qless,), (self.q1,), "div")

    def test_true_divide(self):
        self._test2(
            np.true_divide,
            self.q1,
            (self.q2, self.qs, self.qless),
            (),
            "div",
            convert2=False,
        )

    def test_floor_divide(self):
        self._test2(
            np.floor_divide,
            self.q1,
            (self.q2, self.qs, self.qless),
            (),
            "div",
            convert2=False,
        )

    def test_negative(self):
        self._test1(np.negative, (self.qless, self.q1), ())

    def test_remainder(self):
        self._test2(
            np.remainder,
            self.q1,
            (self.q2, self.qs, self.qless),
            (),
            "same",
            convert2=False,
        )

    def test_mod(self):
        self._test2(
            np.mod, self.q1, (self.q2, self.qs, self.qless), (), "same", convert2=False
        )

    def test_fmod(self):
        self._test2(
            np.fmod, self.q1, (self.q2, self.qs, self.qless), (), "same", convert2=False
        )

    def test_absolute(self):
        self._test1(np.absolute, (self.q2, self.qs, self.qless, self.qi), (), "same")

    def test_rint(self):
        self._test1(np.rint, (self.q2, self.qs, self.qless, self.qi), (), "same")

    def test_conj(self):
        self._test1(np.conj, (self.q2, self.qs, self.qless, self.qi), (), "same")

    def test_exp(self):
        self._test1(np.exp, (self.qless,), (self.q1,), "")

    def test_exp2(self):
        self._test1(np.exp2, (self.qless,), (self.q1,), "")

    def test_log(self):
        self._test1(np.log, (self.qless,), (self.q1,), "")

    def test_log2(self):
        self._test1(np.log2, (self.qless,), (self.q1,), "")

    def test_log10(self):
        self._test1(np.log10, (self.qless,), (self.q1,), "")

    def test_expm1(self):
        self._test1(np.expm1, (self.qless,), (self.q1,), "")

    def test_sqrt(self):
        self._test1(np.sqrt, (self.q2, self.qs, self.qless, self.qi), (), 0.5)

    def test_square(self):
        self._test1(np.square, (self.q2, self.qs, self.qless, self.qi), (), 2)

    def test_reciprocal(self):
        self._test1(np.reciprocal, (self.q2, self.qs, self.qless, self.qi), (), -1)


@helpers.requires_numpy()
class TestTrigUfuncs(TestUFuncs):
    """Universal functions (ufunc) > Trigonometric functions

    http://docs.scipy.org/doc/numpy/reference/ufuncs.html#trigonometric-functions

    sin(x[, out]) 	Trigonometric sine, element-wise.
    cos(x[, out]) 	Cosine elementwise.
    tan(x[, out]) 	Compute tangent element-wise.
    arcsin(x[, out]) 	Inverse sine, element-wise.
    arccos(x[, out]) 	Trigonometric inverse cosine, element-wise.
    arctan(x[, out]) 	Trigonometric inverse tangent, element-wise.
    arctan2(x1, x2[, out]) 	Element-wise arc tangent of x1/x2 choosing the quadrant correctly.
    hypot(x1, x2[, out]) 	Given the “legs” of a right triangle, return its hypotenuse.
    sinh(x[, out]) 	Hyperbolic sine, element-wise.
    cosh(x[, out]) 	Hyperbolic cosine, element-wise.
    tanh(x[, out]) 	Compute hyperbolic tangent element-wise.
    arcsinh(x[, out]) 	Inverse hyperbolic sine elementwise.
    arccosh(x[, out]) 	Inverse hyperbolic cosine, elementwise.
    arctanh(x[, out]) 	Inverse hyperbolic tangent elementwise.
    deg2rad(x[, out]) 	Convert angles from degrees to radians.
    rad2deg(x[, out]) 	Convert angles from radians to degrees.

    Parameters
    ----------

    Returns
    -------

    """

    def test_sin(self):
        self._test1(
            np.sin,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.sin(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.sin,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.sin(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_cos(self):
        self._test1(
            np.cos,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.cos(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.cos,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.cos(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_tan(self):
        self._test1(
            np.tan,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.tan(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.tan,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.tan(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_arcsin(self):
        self._test1(
            np.arcsin,
            (
                np.arange(0, 0.9, 0.1) * self.ureg.dimensionless,
                np.arange(0, 0.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "radian",
        )

    def test_arccos(self):
        self._test1(
            np.arccos,
            (
                np.arange(0, 0.9, 0.1) * self.ureg.dimensionless,
                np.arange(0, 0.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "radian",
        )

    def test_arctan(self):
        self._test1(
            np.arctan,
            (
                np.arange(0, 0.9, 0.1) * self.ureg.dimensionless,
                np.arange(0, 0.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "radian",
        )

    def test_arctan2(self):
        m = self.ureg.m
        j = self.ureg.J
        km = self.ureg.km
        self._test2(
            np.arctan2,
            np.arange(0, 0.9, 0.1) * m,
            (
                np.arange(0, 0.9, 0.1) * m,
                np.arange(0.9, 0.0, -0.1) * m,
                np.arange(0, 0.9, 0.1) * km,
                np.arange(0.9, 0.0, -0.1) * km,
            ),
            raise_with=np.arange(0, 0.9, 0.1) * j,
            output_units="radian",
        )

    def test_hypot(self):
        self.assertTrue(
            np.hypot(3.0 * self.ureg.m, 4.0 * self.ureg.m) == 5.0 * self.ureg.m
        )
        self.assertTrue(
            np.hypot(3.0 * self.ureg.m, 400.0 * self.ureg.cm) == 5.0 * self.ureg.m
        )
        with self.assertRaises(DimensionalityError):
            np.hypot(1.0 * self.ureg.m, 2.0 * self.ureg.J)

    def test_sinh(self):
        self._test1(
            np.sinh,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.sinh(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.sinh,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.sinh(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_cosh(self):
        self._test1(
            np.cosh,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.cosh(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.cosh,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.cosh(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_tanh(self):
        self._test1(
            np.tanh,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "",
            results=(None, None, np.tanh(np.arange(0, pi / 2, pi / 4) * 0.001)),
        )
        self._test1(
            np.tanh,
            (np.rad2deg(np.arange(0, pi / 2, pi / 4)) * self.ureg.degrees,),
            results=(np.tanh(np.arange(0, pi / 2, pi / 4)),),
        )

    def test_arcsinh(self):
        self._test1(
            np.arcsinh,
            (
                np.arange(0, 0.9, 0.1) * self.ureg.dimensionless,
                np.arange(0, 0.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "radian",
        )

    def test_arccosh(self):
        self._test1(
            np.arccosh,
            (
                np.arange(1.0, 1.9, 0.1) * self.ureg.dimensionless,
                np.arange(1.0, 1.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "radian",
        )

    def test_arctanh(self):
        self._test1(
            np.arctanh,
            (
                np.arange(0, 0.9, 0.1) * self.ureg.dimensionless,
                np.arange(0, 0.9, 0.1) * self.ureg.m / self.ureg.m,
            ),
            (0.1 * self.ureg.m,),
            "radian",
        )

    def test_deg2rad(self):
        self._test1(
            np.deg2rad,
            (np.arange(0, pi / 2, pi / 4) * self.ureg.degrees,),
            (1 * self.ureg.m,),
            "radians",
        )

    def test_rad2deg(self):
        self._test1(
            np.rad2deg,
            (
                np.arange(0, pi / 2, pi / 4) * self.ureg.dimensionless,
                np.arange(0, pi / 2, pi / 4) * self.ureg.radian,
                np.arange(0, pi / 2, pi / 4) * self.ureg.mm / self.ureg.m,
            ),
            (1 * self.ureg.m,),
            "degree",
            results=(
                None,
                None,
                np.rad2deg(np.arange(0, pi / 2, pi / 4) * 0.001) * self.ureg.degree,
            ),
        )


class TestComparisonUfuncs(TestUFuncs):
    """Universal functions (ufunc) > Comparison functions

    http://docs.scipy.org/doc/numpy/reference/ufuncs.html#comparison-functions

    greater(x1, x2[, out]) 	Return the truth value of (x1 > x2) element-wise.
    greater_equal(x1, x2[, out]) 	Return the truth value of (x1 >= x2) element-wise.
    less(x1, x2[, out]) 	Return the truth value of (x1 < x2) element-wise.
    less_equal(x1, x2[, out]) 	Return the truth value of (x1 =< x2) element-wise.
    not_equal(x1, x2[, out]) 	Return (x1 != x2) element-wise.
    equal(x1, x2[, out]) 	Return (x1 == x2) element-wise.

    Parameters
    ----------

    Returns
    -------

    """

    def test_greater(self):
        self._testn2(np.greater, self.q1, (self.q2,), (self.qm,))

    def test_greater_equal(self):
        self._testn2(np.greater_equal, self.q1, (self.q2,), (self.qm,))

    def test_less(self):
        self._testn2(np.less, self.q1, (self.q2,), (self.qm,))

    def test_less_equal(self):
        self._testn2(np.less_equal, self.q1, (self.q2,), (self.qm,))

    def test_not_equal(self):
        self._testn2(np.not_equal, self.q1, (self.q2,), (self.qm,))

    def test_equal(self):
        self._testn2(np.equal, self.q1, (self.q2,), (self.qm,))


class TestFloatingUfuncs(TestUFuncs):
    """Universal functions (ufunc) > Floating functions

    http://docs.scipy.org/doc/numpy/reference/ufuncs.html#floating-functions

    isreal(x) 	Returns a bool array, where True if input element is real.
    iscomplex(x) 	Returns a bool array, where True if input element is complex.
    isfinite(x[, out]) 	Test element-wise for finite-ness (not infinity or not Not a Number).
    isinf(x[, out]) 	Test element-wise for positive or negative infinity.
    isnan(x[, out]) 	Test element-wise for Not a Number (NaN), return result as a bool array.
    signbit(x[, out]) 	Returns element-wise True where signbit is set (less than zero).
    copysign(x1, x2[, out]) 	Change the sign of x1 to that of x2, element-wise.
    nextafter(x1, x2[, out]) 	Return the next representable floating-point value after x1 in the direction of x2 element-wise.
    modf(x[, out1, out2]) 	Return the fractional and integral parts of an array, element-wise.
    ldexp(x1, x2[, out]) 	Compute y = x1 * 2**x2.
    frexp(x[, out1, out2]) 	Split the number, x, into a normalized fraction (y1) and exponent (y2)
    fmod(x1, x2[, out]) 	Return the element-wise remainder of division.
    floor(x[, out]) 	Return the floor of the input, element-wise.
    ceil(x[, out]) 	Return the ceiling of the input, element-wise.
    trunc(x[, out]) 	Return the truncated value of the input, element-wise.

    Parameters
    ----------

    Returns
    -------

    """

    def test_isreal(self):
        self._testn(np.isreal, (self.q1, self.qm, self.qless))

    def test_iscomplex(self):
        self._testn(np.iscomplex, (self.q1, self.qm, self.qless))

    def test_isfinite(self):
        self._testn(np.isfinite, (self.q1, self.qm, self.qless))

    def test_isinf(self):
        self._testn(np.isinf, (self.q1, self.qm, self.qless))

    def test_isnan(self):
        self._testn(np.isnan, (self.q1, self.qm, self.qless))

    def test_signbit(self):
        self._testn(np.signbit, (self.q1, self.qm, self.qless))

    def test_copysign(self):
        self._test2(np.copysign, self.q1, (self.q2, self.qs), (self.qm,))

    def test_nextafter(self):
        self._test2(np.nextafter, self.q1, (self.q2, self.qs), (self.qm,))

    def test_modf(self):
        self._test1_2o(np.modf, (self.q2, self.qs))

    def test_ldexp(self):
        x1, x2 = np.frexp(self.q2)
        self._test2(np.ldexp, x1, (x2,))

    def test_frexp(self):
        self._test1_2o(np.frexp, (self.q2, self.qs), output_units=("same", None))

    def test_fmod(self):
        # See TestMathUfuncs.test_fmod
        pass

    def test_floor(self):
        self._test1(np.floor, (self.q1, self.qm, self.qless))

    def test_ceil(self):
        self._test1(np.ceil, (self.q1, self.qm, self.qless))

    def test_trunc(self):
        self._test1(np.trunc, (self.q1, self.qm, self.qless))
