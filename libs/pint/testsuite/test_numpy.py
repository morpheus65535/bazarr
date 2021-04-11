import copy
import operator as op
import pickle
import unittest
import warnings

from pint import DimensionalityError, OffsetUnitCalculusError, UnitStrippedWarning
from pint.compat import np
from pint.testsuite import QuantityTestCase, helpers
from pint.testsuite.test_umath import TestUFuncs


@helpers.requires_numpy()
class TestNumpyMethods(QuantityTestCase):

    FORCE_NDARRAY = True

    @classmethod
    def setUpClass(cls):
        from pint import _DEFAULT_REGISTRY

        cls.ureg = _DEFAULT_REGISTRY
        cls.Q_ = cls.ureg.Quantity

    @property
    def q(self):
        return [[1, 2], [3, 4]] * self.ureg.m

    @property
    def q_nan(self):
        return [[1, 2], [3, np.nan]] * self.ureg.m

    @property
    def q_zero_or_nan(self):
        return [[0, 0], [0, np.nan]] * self.ureg.m

    @property
    def q_temperature(self):
        return self.Q_([[1, 2], [3, 4]], self.ureg.degC)

    def assertNDArrayEqual(self, actual, desired):
        # Assert that the given arrays are equal, and are not Quantities
        np.testing.assert_array_equal(actual, desired)
        self.assertFalse(isinstance(actual, self.Q_))
        self.assertFalse(isinstance(desired, self.Q_))


class TestNumpyArrayCreation(TestNumpyMethods):
    # https://docs.scipy.org/doc/numpy/reference/routines.array-creation.html

    @helpers.requires_array_function_protocol()
    def test_ones_like(self):
        self.assertNDArrayEqual(np.ones_like(self.q), np.array([[1, 1], [1, 1]]))

    @helpers.requires_array_function_protocol()
    def test_zeros_like(self):
        self.assertNDArrayEqual(np.zeros_like(self.q), np.array([[0, 0], [0, 0]]))

    @helpers.requires_array_function_protocol()
    def test_empty_like(self):
        ret = np.empty_like(self.q)
        self.assertEqual(ret.shape, (2, 2))
        self.assertTrue(isinstance(ret, np.ndarray))

    @helpers.requires_array_function_protocol()
    def test_full_like(self):
        self.assertQuantityEqual(
            np.full_like(self.q, self.Q_(0, self.ureg.degC)),
            self.Q_([[0, 0], [0, 0]], self.ureg.degC),
        )
        self.assertNDArrayEqual(np.full_like(self.q, 2), np.array([[2, 2], [2, 2]]))


class TestNumpyArrayManipulation(TestNumpyMethods):
    # TODO
    # https://www.numpy.org/devdocs/reference/routines.array-manipulation.html
    # copyto
    # broadcast , broadcast_arrays
    # asarray	asanyarray	asmatrix	asfarray	asfortranarray	ascontiguousarray	asarray_chkfinite	asscalar	require

    # Changing array shape

    def test_flatten(self):
        self.assertQuantityEqual(self.q.flatten(), [1, 2, 3, 4] * self.ureg.m)

    def test_flat(self):
        for q, v in zip(self.q.flat, [1, 2, 3, 4]):
            self.assertEqual(q, v * self.ureg.m)

    def test_reshape(self):
        self.assertQuantityEqual(self.q.reshape([1, 4]), [[1, 2, 3, 4]] * self.ureg.m)

    def test_ravel(self):
        self.assertQuantityEqual(self.q.ravel(), [1, 2, 3, 4] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_ravel_numpy_func(self):
        self.assertQuantityEqual(np.ravel(self.q), [1, 2, 3, 4] * self.ureg.m)

    # Transpose-like operations

    @helpers.requires_array_function_protocol()
    def test_moveaxis(self):
        self.assertQuantityEqual(
            np.moveaxis(self.q, 1, 0), np.array([[1, 2], [3, 4]]).T * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_rollaxis(self):
        self.assertQuantityEqual(
            np.rollaxis(self.q, 1), np.array([[1, 2], [3, 4]]).T * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_swapaxes(self):
        self.assertQuantityEqual(
            np.swapaxes(self.q, 1, 0), np.array([[1, 2], [3, 4]]).T * self.ureg.m
        )

    def test_transpose(self):
        self.assertQuantityEqual(self.q.transpose(), [[1, 3], [2, 4]] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_transpose_numpy_func(self):
        self.assertQuantityEqual(np.transpose(self.q), [[1, 3], [2, 4]] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_flip_numpy_func(self):
        self.assertQuantityEqual(
            np.flip(self.q, axis=0), [[3, 4], [1, 2]] * self.ureg.m
        )

    # Changing number of dimensions

    @helpers.requires_array_function_protocol()
    def test_atleast_1d(self):
        actual = np.atleast_1d(self.Q_(0, self.ureg.degC), self.q.flatten())
        expected = (self.Q_(np.array([0]), self.ureg.degC), self.q.flatten())
        for ind_actual, ind_expected in zip(actual, expected):
            self.assertQuantityEqual(ind_actual, ind_expected)
        self.assertQuantityEqual(np.atleast_1d(self.q), self.q)

    @helpers.requires_array_function_protocol()
    def test_atleast_2d(self):
        actual = np.atleast_2d(self.Q_(0, self.ureg.degC), self.q.flatten())
        expected = (
            self.Q_(np.array([[0]]), self.ureg.degC),
            np.array([[1, 2, 3, 4]]) * self.ureg.m,
        )
        for ind_actual, ind_expected in zip(actual, expected):
            self.assertQuantityEqual(ind_actual, ind_expected)
        self.assertQuantityEqual(np.atleast_2d(self.q), self.q)

    @helpers.requires_array_function_protocol()
    def test_atleast_3d(self):
        actual = np.atleast_3d(self.Q_(0, self.ureg.degC), self.q.flatten())
        expected = (
            self.Q_(np.array([[[0]]]), self.ureg.degC),
            np.array([[[1], [2], [3], [4]]]) * self.ureg.m,
        )
        for ind_actual, ind_expected in zip(actual, expected):
            self.assertQuantityEqual(ind_actual, ind_expected)
        self.assertQuantityEqual(
            np.atleast_3d(self.q), np.array([[[1], [2]], [[3], [4]]]) * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_broadcast_to(self):
        self.assertQuantityEqual(
            np.broadcast_to(self.q[:, 1], (2, 2)),
            np.array([[2, 4], [2, 4]]) * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_expand_dims(self):
        self.assertQuantityEqual(
            np.expand_dims(self.q, 0), np.array([[[1, 2], [3, 4]]]) * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_squeeze(self):
        self.assertQuantityEqual(np.squeeze(self.q), self.q)
        self.assertQuantityEqual(
            self.q.reshape([1, 4]).squeeze(), [1, 2, 3, 4] * self.ureg.m
        )

    # Changing number of dimensions
    # Joining arrays
    @helpers.requires_array_function_protocol()
    def test_concat_stack(self):
        for func in (np.concatenate, np.stack, np.hstack, np.vstack, np.dstack):
            with self.subTest(func=func):
                self.assertQuantityEqual(
                    func([self.q] * 2), self.Q_(func([self.q.m] * 2), self.ureg.m)
                )
                # One or more of the args is a bare array full of zeros or NaNs
                self.assertQuantityEqual(
                    func([self.q_zero_or_nan.m, self.q]),
                    self.Q_(func([self.q_zero_or_nan.m, self.q.m]), self.ureg.m),
                )
                # One or more of the args is a bare array with at least one non-zero,
                # non-NaN element
                nz = self.q_zero_or_nan
                nz.m[0, 0] = 1
                with self.assertRaises(DimensionalityError):
                    func([nz.m, self.q])

    @helpers.requires_array_function_protocol()
    def test_block_column_stack(self):
        for func in (np.block, np.column_stack):
            with self.subTest(func=func):

                self.assertQuantityEqual(
                    func([self.q[:, 0], self.q[:, 1]]),
                    self.Q_(func([self.q[:, 0].m, self.q[:, 1].m]), self.ureg.m),
                )

                # One or more of the args is a bare array full of zeros or NaNs
                self.assertQuantityEqual(
                    func(
                        [
                            self.q_zero_or_nan[:, 0].m,
                            self.q[:, 0],
                            self.q_zero_or_nan[:, 1].m,
                        ]
                    ),
                    self.Q_(
                        func(
                            [
                                self.q_zero_or_nan[:, 0].m,
                                self.q[:, 0].m,
                                self.q_zero_or_nan[:, 1].m,
                            ]
                        ),
                        self.ureg.m,
                    ),
                )
                # One or more of the args is a bare array with at least one non-zero,
                # non-NaN element
                nz = self.q_zero_or_nan
                nz.m[0, 0] = 1
                with self.assertRaises(DimensionalityError):
                    func([nz[:, 0].m, self.q[:, 0]])

    @helpers.requires_array_function_protocol()
    def test_append(self):
        self.assertQuantityEqual(
            np.append(self.q, [[0, 0]] * self.ureg.m, axis=0),
            [[1, 2], [3, 4], [0, 0]] * self.ureg.m,
        )

    def test_astype(self):
        actual = self.q.astype(np.float32)
        expected = self.Q_(np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32), "m")
        self.assertQuantityEqual(actual, expected)
        self.assertEqual(actual.m.dtype, expected.m.dtype)

    def test_item(self):
        self.assertQuantityEqual(self.Q_([[0]], "m").item(), 0 * self.ureg.m)


class TestNumpyMathematicalFunctions(TestNumpyMethods):
    # https://www.numpy.org/devdocs/reference/routines.math.html
    # Trigonometric functions
    @helpers.requires_array_function_protocol()
    def test_unwrap(self):
        self.assertQuantityEqual(
            np.unwrap([0, 3 * np.pi] * self.ureg.radians), [0, np.pi]
        )
        self.assertQuantityEqual(
            np.unwrap([0, 540] * self.ureg.deg), [0, 180] * self.ureg.deg
        )

    # Rounding

    @helpers.requires_array_function_protocol()
    def test_fix(self):
        self.assertQuantityEqual(np.fix(3.14 * self.ureg.m), 3.0 * self.ureg.m)
        self.assertQuantityEqual(np.fix(3.0 * self.ureg.m), 3.0 * self.ureg.m)
        self.assertQuantityEqual(
            np.fix([2.1, 2.9, -2.1, -2.9] * self.ureg.m),
            [2.0, 2.0, -2.0, -2.0] * self.ureg.m,
        )

    # Sums, products, differences

    @helpers.requires_array_function_protocol()
    def test_prod(self):
        axis = 0
        where = [[True, False], [True, True]]

        self.assertQuantityEqual(self.q.prod(), 24 * self.ureg.m ** 4)
        self.assertQuantityEqual(self.q.prod(axis=axis), [3, 8] * self.ureg.m ** 2)
        self.assertQuantityEqual(self.q.prod(where=where), 12 * self.ureg.m ** 3)

    @helpers.requires_array_function_protocol()
    def test_prod_numpy_func(self):
        axis = 0
        where = [[True, False], [True, True]]

        self.assertQuantityEqual(np.prod(self.q), 24 * self.ureg.m ** 4)
        self.assertQuantityEqual(np.prod(self.q, axis=axis), [3, 8] * self.ureg.m ** 2)
        self.assertQuantityEqual(np.prod(self.q, where=where), 12 * self.ureg.m ** 3)

        self.assertRaises(DimensionalityError, np.prod, self.q, axis=axis, where=where)
        self.assertQuantityEqual(
            np.prod(self.q, axis=axis, where=[[True, False], [False, True]]),
            [1, 4] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.prod(self.q, axis=axis, where=[True, False]), [3, 1] * self.ureg.m ** 2
        )

    def test_sum(self):
        self.assertEqual(self.q.sum(), 10 * self.ureg.m)
        self.assertQuantityEqual(self.q.sum(0), [4, 6] * self.ureg.m)
        self.assertQuantityEqual(self.q.sum(1), [3, 7] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_sum_numpy_func(self):
        self.assertQuantityEqual(np.sum(self.q, axis=0), [4, 6] * self.ureg.m)
        self.assertRaises(OffsetUnitCalculusError, np.sum, self.q_temperature)

    @helpers.requires_array_function_protocol()
    def test_nansum_numpy_func(self):
        self.assertQuantityEqual(np.nansum(self.q_nan, axis=0), [4, 2] * self.ureg.m)

    def test_cumprod(self):
        self.assertRaises(DimensionalityError, self.q.cumprod)
        self.assertQuantityEqual((self.q / self.ureg.m).cumprod(), [1, 2, 6, 24])

    @helpers.requires_array_function_protocol()
    def test_cumprod_numpy_func(self):
        self.assertRaises(DimensionalityError, np.cumprod, self.q)
        self.assertRaises(DimensionalityError, np.cumproduct, self.q)
        self.assertQuantityEqual(np.cumprod(self.q / self.ureg.m), [1, 2, 6, 24])
        self.assertQuantityEqual(np.cumproduct(self.q / self.ureg.m), [1, 2, 6, 24])
        self.assertQuantityEqual(
            np.cumprod(self.q / self.ureg.m, axis=1), [[1, 2], [3, 12]]
        )

    @helpers.requires_array_function_protocol()
    def test_nancumprod_numpy_func(self):
        self.assertRaises(DimensionalityError, np.nancumprod, self.q_nan)
        self.assertQuantityEqual(np.nancumprod(self.q_nan / self.ureg.m), [1, 2, 6, 6])

    @helpers.requires_array_function_protocol()
    def test_diff(self):
        self.assertQuantityEqual(np.diff(self.q, 1), [[1], [1]] * self.ureg.m)
        self.assertQuantityEqual(
            np.diff(self.q_temperature, 1), [[1], [1]] * self.ureg.delta_degC
        )

    @helpers.requires_array_function_protocol()
    def test_ediff1d(self):
        self.assertQuantityEqual(np.ediff1d(self.q), [1, 1, 1] * self.ureg.m)
        self.assertQuantityEqual(
            np.ediff1d(self.q_temperature), [1, 1, 1] * self.ureg.delta_degC
        )

    @helpers.requires_array_function_protocol()
    def test_gradient(self):
        grad = np.gradient([[1, 1], [3, 4]] * self.ureg.m, 1 * self.ureg.J)
        self.assertQuantityEqual(
            grad[0], [[2.0, 3.0], [2.0, 3.0]] * self.ureg.m / self.ureg.J
        )
        self.assertQuantityEqual(
            grad[1], [[0.0, 0.0], [1.0, 1.0]] * self.ureg.m / self.ureg.J
        )

        grad = np.gradient(self.Q_([[1, 1], [3, 4]], self.ureg.degC), 1 * self.ureg.J)
        self.assertQuantityEqual(
            grad[0], [[2.0, 3.0], [2.0, 3.0]] * self.ureg.delta_degC / self.ureg.J
        )
        self.assertQuantityEqual(
            grad[1], [[0.0, 0.0], [1.0, 1.0]] * self.ureg.delta_degC / self.ureg.J
        )

    @helpers.requires_array_function_protocol()
    def test_cross(self):
        a = [[3, -3, 1]] * self.ureg.kPa
        b = [[4, 9, 2]] * self.ureg.m ** 2
        self.assertQuantityEqual(
            np.cross(a, b), [[-15, -2, 39]] * self.ureg.kPa * self.ureg.m ** 2
        )

    @helpers.requires_array_function_protocol()
    def test_trapz(self):
        self.assertQuantityEqual(
            np.trapz([1.0, 2.0, 3.0, 4.0] * self.ureg.J, dx=1 * self.ureg.m),
            7.5 * self.ureg.J * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_dot(self):
        self.assertQuantityEqual(
            self.q.ravel().dot(np.array([1, 0, 0, 1])), 5 * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_dot_numpy_func(self):
        self.assertQuantityEqual(
            np.dot(self.q.ravel(), [0, 0, 1, 0] * self.ureg.dimensionless),
            3 * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_einsum(self):
        a = np.arange(25).reshape(5, 5) * self.ureg.m
        b = np.arange(5) * self.ureg.m
        self.assertQuantityEqual(np.einsum("ii", a), 60 * self.ureg.m)
        self.assertQuantityEqual(
            np.einsum("ii->i", a), np.array([0, 6, 12, 18, 24]) * self.ureg.m
        )
        self.assertQuantityEqual(np.einsum("i,i", b, b), 30 * self.ureg.m ** 2)
        self.assertQuantityEqual(
            np.einsum("ij,j", a, b),
            np.array([30, 80, 130, 180, 230]) * self.ureg.m ** 2,
        )

    @helpers.requires_array_function_protocol()
    def test_solve(self):
        self.assertQuantityAlmostEqual(
            np.linalg.solve(self.q, [[3], [7]] * self.ureg.s),
            self.Q_([[1], [1]], "m / s"),
        )

    # Arithmetic operations
    def test_addition_with_scalar(self):
        a = np.array([0, 1, 2])
        b = 10.0 * self.ureg("gram/kilogram")
        self.assertQuantityAlmostEqual(
            a + b, self.Q_([0.01, 1.01, 2.01], self.ureg.dimensionless)
        )
        self.assertQuantityAlmostEqual(
            b + a, self.Q_([0.01, 1.01, 2.01], self.ureg.dimensionless)
        )

    def test_addition_with_incompatible_scalar(self):
        a = np.array([0, 1, 2])
        b = 1.0 * self.ureg.m
        self.assertRaises(DimensionalityError, op.add, a, b)
        self.assertRaises(DimensionalityError, op.add, b, a)

    def test_power(self):
        arr = np.array(range(3), dtype=np.float)
        q = self.Q_(arr, "meter")

        for op_ in [op.pow, op.ipow, np.power]:
            q_cp = copy.copy(q)
            self.assertRaises(DimensionalityError, op_, 2.0, q_cp)
            arr_cp = copy.copy(arr)
            arr_cp = copy.copy(arr)
            q_cp = copy.copy(q)
            self.assertRaises(DimensionalityError, op_, q_cp, arr_cp)
            q_cp = copy.copy(q)
            q2_cp = copy.copy(q)
            self.assertRaises(DimensionalityError, op_, q_cp, q2_cp)

        self.assertQuantityEqual(
            np.power(self.q, self.Q_(2)), self.Q_([[1, 4], [9, 16]], "m**2")
        )
        self.assertQuantityEqual(
            self.q ** self.Q_(2), self.Q_([[1, 4], [9, 16]], "m**2")
        )
        self.assertNDArrayEqual(arr ** self.Q_(2), np.array([0, 1, 4]))

    def test_sqrt(self):
        q = self.Q_(100, "m**2")
        self.assertQuantityEqual(np.sqrt(q), self.Q_(10, "m"))

    def test_cbrt(self):
        q = self.Q_(1000, "m**3")
        self.assertQuantityEqual(np.cbrt(q), self.Q_(10, "m"))

    @unittest.expectedFailure
    @helpers.requires_numpy()
    def test_exponentiation_array_exp_2(self):
        arr = np.array(range(3), dtype=np.float)
        # q = self.Q_(copy.copy(arr), None)
        q = self.Q_(copy.copy(arr), "meter")
        arr_cp = copy.copy(arr)
        q_cp = copy.copy(q)
        # this fails as expected since numpy 1.8.0 but...
        self.assertRaises(DimensionalityError, op.pow, arr_cp, q_cp)
        # ..not for op.ipow !
        # q_cp is treated as if it is an array. The units are ignored.
        # Quantity.__ipow__ is never called
        arr_cp = copy.copy(arr)
        q_cp = copy.copy(q)
        self.assertRaises(DimensionalityError, op.ipow, arr_cp, q_cp)


class TestNumpyUnclassified(TestNumpyMethods):
    def test_tolist(self):
        self.assertEqual(
            self.q.tolist(),
            [[1 * self.ureg.m, 2 * self.ureg.m], [3 * self.ureg.m, 4 * self.ureg.m]],
        )

    def test_fill(self):
        tmp = self.q
        tmp.fill(6 * self.ureg.ft)
        self.assertQuantityEqual(tmp, [[6, 6], [6, 6]] * self.ureg.ft)
        tmp.fill(5 * self.ureg.m)
        self.assertQuantityEqual(tmp, [[5, 5], [5, 5]] * self.ureg.m)

    def test_take(self):
        self.assertQuantityEqual(self.q.take([0, 1, 2, 3]), self.q.flatten())

    def test_put(self):
        q = [1.0, 2.0, 3.0, 4.0] * self.ureg.m
        q.put([0, 2], [10.0, 20.0] * self.ureg.m)
        self.assertQuantityEqual(q, [10.0, 2.0, 20.0, 4.0] * self.ureg.m)

        q = [1.0, 2.0, 3.0, 4.0] * self.ureg.m
        q.put([0, 2], [1.0, 2.0] * self.ureg.mm)
        self.assertQuantityEqual(q, [0.001, 2.0, 0.002, 4.0] * self.ureg.m)

        q = [1.0, 2.0, 3.0, 4.0] * self.ureg.m / self.ureg.mm
        q.put([0, 2], [1.0, 2.0])
        self.assertQuantityEqual(
            q, [0.001, 2.0, 0.002, 4.0] * self.ureg.m / self.ureg.mm
        )

        q = [1.0, 2.0, 3.0, 4.0] * self.ureg.m
        with self.assertRaises(DimensionalityError):
            q.put([0, 2], [4.0, 6.0] * self.ureg.J)
        with self.assertRaises(DimensionalityError):
            q.put([0, 2], [4.0, 6.0])

    def test_repeat(self):
        self.assertQuantityEqual(
            self.q.repeat(2), [1, 1, 2, 2, 3, 3, 4, 4] * self.ureg.m
        )

    def test_sort(self):
        q = [4, 5, 2, 3, 1, 6] * self.ureg.m
        q.sort()
        self.assertQuantityEqual(q, [1, 2, 3, 4, 5, 6] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_sort_numpy_func(self):
        q = [4, 5, 2, 3, 1, 6] * self.ureg.m
        self.assertQuantityEqual(np.sort(q), [1, 2, 3, 4, 5, 6] * self.ureg.m)

    def test_argsort(self):
        q = [1, 4, 5, 6, 2, 9] * self.ureg.MeV
        self.assertNDArrayEqual(q.argsort(), [0, 4, 1, 2, 3, 5])

    @helpers.requires_array_function_protocol()
    def test_argsort_numpy_func(self):
        self.assertNDArrayEqual(np.argsort(self.q, axis=0), np.array([[0, 0], [1, 1]]))

    def test_diagonal(self):
        q = [[1, 2, 3], [1, 2, 3], [1, 2, 3]] * self.ureg.m
        self.assertQuantityEqual(q.diagonal(offset=1), [2, 3] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_diagonal_numpy_func(self):
        q = [[1, 2, 3], [1, 2, 3], [1, 2, 3]] * self.ureg.m
        self.assertQuantityEqual(np.diagonal(q, offset=-1), [1, 2] * self.ureg.m)

    def test_compress(self):
        self.assertQuantityEqual(
            self.q.compress([False, True], axis=0), [[3, 4]] * self.ureg.m
        )
        self.assertQuantityEqual(
            self.q.compress([False, True], axis=1), [[2], [4]] * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_compress_nep18(self):
        self.assertQuantityEqual(
            np.compress([False, True], self.q, axis=1), [[2], [4]] * self.ureg.m
        )

    def test_searchsorted(self):
        q = self.q.flatten()
        self.assertNDArrayEqual(q.searchsorted([1.5, 2.5] * self.ureg.m), [1, 2])
        q = self.q.flatten()
        self.assertRaises(DimensionalityError, q.searchsorted, [1.5, 2.5])

    @helpers.requires_array_function_protocol()
    def test_searchsorted_numpy_func(self):
        """Test searchsorted as numpy function."""
        q = self.q.flatten()
        self.assertNDArrayEqual(np.searchsorted(q, [1.5, 2.5] * self.ureg.m), [1, 2])

    def test_nonzero(self):
        q = [1, 0, 5, 6, 0, 9] * self.ureg.m
        self.assertNDArrayEqual(q.nonzero()[0], [0, 2, 3, 5])

    @helpers.requires_array_function_protocol()
    def test_nonzero_numpy_func(self):
        q = [1, 0, 5, 6, 0, 9] * self.ureg.m
        self.assertNDArrayEqual(np.nonzero(q)[0], [0, 2, 3, 5])

    @helpers.requires_array_function_protocol()
    def test_any_numpy_func(self):
        q = [0, 1] * self.ureg.m
        self.assertTrue(np.any(q))
        self.assertRaises(ValueError, np.any, self.q_temperature)

    @helpers.requires_array_function_protocol()
    def test_all_numpy_func(self):
        q = [0, 1] * self.ureg.m
        self.assertFalse(np.all(q))
        self.assertRaises(ValueError, np.all, self.q_temperature)

    @helpers.requires_array_function_protocol()
    def test_count_nonzero_numpy_func(self):
        q = [1, 0, 5, 6, 0, 9] * self.ureg.m
        self.assertEqual(np.count_nonzero(q), 4)

    def test_max(self):
        self.assertEqual(self.q.max(), 4 * self.ureg.m)

    def test_max_numpy_func(self):
        self.assertEqual(np.max(self.q), 4 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_max_with_axis_arg(self):
        self.assertQuantityEqual(np.max(self.q, axis=1), [2, 4] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_max_with_initial_arg(self):
        self.assertQuantityEqual(
            np.max(self.q[..., None], axis=2, initial=3 * self.ureg.m),
            [[3, 3], [3, 4]] * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_nanmax(self):
        self.assertEqual(np.nanmax(self.q_nan), 3 * self.ureg.m)

    def test_argmax(self):
        self.assertEqual(self.q.argmax(), 3)

    @helpers.requires_array_function_protocol()
    def test_argmax_numpy_func(self):
        self.assertNDArrayEqual(np.argmax(self.q, axis=0), np.array([1, 1]))

    @helpers.requires_array_function_protocol()
    def test_nanargmax_numpy_func(self):
        self.assertNDArrayEqual(np.nanargmax(self.q_nan, axis=0), np.array([1, 0]))

    def test_maximum(self):
        self.assertQuantityEqual(
            np.maximum(self.q, self.Q_([0, 5], "m")), self.Q_([[1, 5], [3, 5]], "m")
        )

    def test_min(self):
        self.assertEqual(self.q.min(), 1 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_min_numpy_func(self):
        self.assertEqual(np.min(self.q), 1 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_min_with_axis_arg(self):
        self.assertQuantityEqual(np.min(self.q, axis=1), [1, 3] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_min_with_initial_arg(self):
        self.assertQuantityEqual(
            np.min(self.q[..., None], axis=2, initial=3 * self.ureg.m),
            [[1, 2], [3, 3]] * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_nanmin(self):
        self.assertEqual(np.nanmin(self.q_nan), 1 * self.ureg.m)

    def test_argmin(self):
        self.assertEqual(self.q.argmin(), 0)

    @helpers.requires_array_function_protocol()
    def test_argmin_numpy_func(self):
        self.assertNDArrayEqual(np.argmin(self.q, axis=0), np.array([0, 0]))

    @helpers.requires_array_function_protocol()
    def test_nanargmin_numpy_func(self):
        self.assertNDArrayEqual(np.nanargmin(self.q_nan, axis=0), np.array([0, 0]))

    def test_minimum(self):
        self.assertQuantityEqual(
            np.minimum(self.q, self.Q_([0, 5], "m")), self.Q_([[0, 2], [0, 4]], "m")
        )

    def test_ptp(self):
        self.assertEqual(self.q.ptp(), 3 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_ptp_numpy_func(self):
        self.assertQuantityEqual(np.ptp(self.q, axis=0), [2, 2] * self.ureg.m)

    def test_clip(self):
        self.assertQuantityEqual(
            self.q.clip(max=2 * self.ureg.m), [[1, 2], [2, 2]] * self.ureg.m
        )
        self.assertQuantityEqual(
            self.q.clip(min=3 * self.ureg.m), [[3, 3], [3, 4]] * self.ureg.m
        )
        self.assertQuantityEqual(
            self.q.clip(min=2 * self.ureg.m, max=3 * self.ureg.m),
            [[2, 2], [3, 3]] * self.ureg.m,
        )
        self.assertRaises(DimensionalityError, self.q.clip, self.ureg.J)
        self.assertRaises(DimensionalityError, self.q.clip, 1)

    @helpers.requires_array_function_protocol()
    def test_clip_numpy_func(self):
        self.assertQuantityEqual(
            np.clip(self.q, 150 * self.ureg.cm, None), [[1.5, 2], [3, 4]] * self.ureg.m
        )

    def test_round(self):
        q = [1, 1.33, 5.67, 22] * self.ureg.m
        self.assertQuantityEqual(q.round(0), [1, 1, 6, 22] * self.ureg.m)
        self.assertQuantityEqual(q.round(-1), [0, 0, 10, 20] * self.ureg.m)
        self.assertQuantityEqual(q.round(1), [1, 1.3, 5.7, 22] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_round_numpy_func(self):
        self.assertQuantityEqual(
            np.around(1.0275 * self.ureg.m, decimals=2), 1.03 * self.ureg.m
        )
        self.assertQuantityEqual(
            np.round_(1.0275 * self.ureg.m, decimals=2), 1.03 * self.ureg.m
        )

    def test_trace(self):
        self.assertEqual(self.q.trace(), (1 + 4) * self.ureg.m)

    def test_cumsum(self):
        self.assertQuantityEqual(self.q.cumsum(), [1, 3, 6, 10] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_cumsum_numpy_func(self):
        self.assertQuantityEqual(
            np.cumsum(self.q, axis=0), [[1, 2], [4, 6]] * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_nancumsum_numpy_func(self):
        self.assertQuantityEqual(
            np.nancumsum(self.q_nan, axis=0), [[1, 2], [4, 2]] * self.ureg.m
        )

    def test_mean(self):
        self.assertEqual(self.q.mean(), 2.5 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_mean_numpy_func(self):
        self.assertEqual(np.mean(self.q), 2.5 * self.ureg.m)
        self.assertEqual(np.mean(self.q_temperature), self.Q_(2.5, self.ureg.degC))

    @helpers.requires_array_function_protocol()
    def test_nanmean_numpy_func(self):
        self.assertEqual(np.nanmean(self.q_nan), 2 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_average_numpy_func(self):
        self.assertQuantityAlmostEqual(
            np.average(self.q, axis=0, weights=[1, 2]),
            [2.33333, 3.33333] * self.ureg.m,
            rtol=1e-5,
        )

    @helpers.requires_array_function_protocol()
    def test_median_numpy_func(self):
        self.assertEqual(np.median(self.q), 2.5 * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_nanmedian_numpy_func(self):
        self.assertEqual(np.nanmedian(self.q_nan), 2 * self.ureg.m)

    def test_var(self):
        self.assertEqual(self.q.var(), 1.25 * self.ureg.m ** 2)

    @helpers.requires_array_function_protocol()
    def test_var_numpy_func(self):
        self.assertEqual(np.var(self.q), 1.25 * self.ureg.m ** 2)

    @helpers.requires_array_function_protocol()
    def test_nanvar_numpy_func(self):
        self.assertQuantityAlmostEqual(
            np.nanvar(self.q_nan), 0.66667 * self.ureg.m ** 2, rtol=1e-5
        )

    def test_std(self):
        self.assertQuantityAlmostEqual(self.q.std(), 1.11803 * self.ureg.m, rtol=1e-5)

    @helpers.requires_array_function_protocol()
    def test_std_numpy_func(self):
        self.assertQuantityAlmostEqual(np.std(self.q), 1.11803 * self.ureg.m, rtol=1e-5)
        self.assertRaises(OffsetUnitCalculusError, np.std, self.q_temperature)

    def test_cumprod(self):
        self.assertRaises(DimensionalityError, self.q.cumprod)
        self.assertQuantityEqual((self.q / self.ureg.m).cumprod(), [1, 2, 6, 24])

    @helpers.requires_array_function_protocol()
    def test_nanstd_numpy_func(self):
        self.assertQuantityAlmostEqual(
            np.nanstd(self.q_nan), 0.81650 * self.ureg.m, rtol=1e-5
        )

    def test_conj(self):
        self.assertQuantityEqual((self.q * (1 + 1j)).conj(), self.q * (1 - 1j))
        self.assertQuantityEqual((self.q * (1 + 1j)).conjugate(), self.q * (1 - 1j))

    def test_getitem(self):
        self.assertRaises(IndexError, self.q.__getitem__, (0, 10))
        self.assertQuantityEqual(self.q[0], [1, 2] * self.ureg.m)
        self.assertEqual(self.q[1, 1], 4 * self.ureg.m)

    def test_setitem(self):
        with self.assertRaises(TypeError):
            self.q[0, 0] = 1
        with self.assertRaises(DimensionalityError):
            self.q[0, 0] = 1 * self.ureg.J
        with self.assertRaises(DimensionalityError):
            self.q[0] = 1
        with self.assertRaises(DimensionalityError):
            self.q[0] = np.ndarray([1, 2])
        with self.assertRaises(DimensionalityError):
            self.q[0] = 1 * self.ureg.J

        q = self.q.copy()
        q[0] = 1 * self.ureg.m
        self.assertQuantityEqual(q, [[1, 1], [3, 4]] * self.ureg.m)

        q = self.q.copy()
        q[...] = 1 * self.ureg.m
        self.assertQuantityEqual(q, [[1, 1], [1, 1]] * self.ureg.m)

        q = self.q.copy()
        q[:] = 1 * self.ureg.m
        self.assertQuantityEqual(q, [[1, 1], [1, 1]] * self.ureg.m)

        # check and see that dimensionless num  bers work correctly
        q = [0, 1, 2, 3] * self.ureg.dimensionless
        q[0] = 1
        self.assertQuantityEqual(q, np.asarray([1, 1, 2, 3]))
        q[0] = self.ureg.m / self.ureg.mm
        self.assertQuantityEqual(q, np.asarray([1000, 1, 2, 3]))

        q = [0.0, 1.0, 2.0, 3.0] * self.ureg.m / self.ureg.mm
        q[0] = 1.0
        self.assertQuantityEqual(q, [0.001, 1, 2, 3] * self.ureg.m / self.ureg.mm)

        # Check that this properly masks the first item without warning
        q = self.ureg.Quantity(
            np.ma.array([0.0, 1.0, 2.0, 3.0], mask=[False, True, False, False]), "m"
        )
        with warnings.catch_warnings(record=True) as w:
            q[0] = np.ma.masked
            # Check for no warnings
            assert not w
            assert q.mask[0]

    def test_iterator(self):
        for q, v in zip(self.q.flatten(), [1, 2, 3, 4]):
            self.assertEqual(q, v * self.ureg.m)

    def test_iterable(self):
        self.assertTrue(np.iterable(self.q))
        self.assertFalse(np.iterable(1 * self.ureg.m))

    def test_reversible_op(self):
        """ """
        x = self.q.magnitude
        u = self.Q_(np.ones(x.shape))
        self.assertQuantityEqual(x / self.q, u * x / self.q)
        self.assertQuantityEqual(x * self.q, u * x * self.q)
        self.assertQuantityEqual(x + u, u + x)
        self.assertQuantityEqual(x - u, -(u - x))

    def test_pickle(self):
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(protocol):
                q1 = [10, 20] * self.ureg.m
                q2 = pickle.loads(pickle.dumps(q1, protocol))
                self.assertNDArrayEqual(q1.magnitude, q2.magnitude)
                self.assertEqual(q1.units, q2.units)

    def test_equal(self):
        x = self.q.magnitude
        u = self.Q_(np.ones(x.shape))
        true = np.ones_like(x, dtype=np.bool_)
        false = np.zeros_like(x, dtype=np.bool_)

        self.assertQuantityEqual(u, u)
        self.assertQuantityEqual(u == u, u.magnitude == u.magnitude)
        self.assertQuantityEqual(u == 1, u.magnitude == 1)

        v = self.Q_(np.zeros(x.shape), "m")
        w = self.Q_(np.ones(x.shape), "m")
        self.assertNDArrayEqual(v == 1, false)
        self.assertNDArrayEqual(
            self.Q_(np.zeros_like(x), "m") == self.Q_(np.zeros_like(x), "s"), false,
        )
        self.assertNDArrayEqual(v == v, true)
        self.assertNDArrayEqual(v == w, false)
        self.assertNDArrayEqual(v == w.to("mm"), false)
        self.assertNDArrayEqual(u == v, false)

    def test_shape(self):
        u = self.Q_(np.arange(12))
        u.shape = 4, 3
        self.assertEqual(u.magnitude.shape, (4, 3))

    @helpers.requires_array_function_protocol()
    def test_shape_numpy_func(self):
        self.assertEqual(np.shape(self.q), (2, 2))

    @helpers.requires_array_function_protocol()
    def test_alen_numpy_func(self):
        self.assertEqual(np.alen(self.q), 2)

    @helpers.requires_array_function_protocol()
    def test_ndim_numpy_func(self):
        self.assertEqual(np.ndim(self.q), 2)

    @helpers.requires_array_function_protocol()
    def test_copy_numpy_func(self):
        q_copy = np.copy(self.q)
        self.assertQuantityEqual(self.q, q_copy)
        self.assertIsNot(self.q, q_copy)

    @helpers.requires_array_function_protocol()
    def test_trim_zeros_numpy_func(self):
        q = [0, 4, 3, 0, 2, 2, 0, 0, 0] * self.ureg.m
        self.assertQuantityEqual(np.trim_zeros(q), [4, 3, 0, 2, 2] * self.ureg.m)

    @helpers.requires_array_function_protocol()
    def test_result_type_numpy_func(self):
        self.assertEqual(np.result_type(self.q), np.dtype("int"))

    @helpers.requires_array_function_protocol()
    def test_nan_to_num_numpy_func(self):
        self.assertQuantityEqual(
            np.nan_to_num(self.q_nan, nan=-999 * self.ureg.mm),
            [[1, 2], [3, -0.999]] * self.ureg.m,
        )

    @helpers.requires_array_function_protocol()
    def test_meshgrid_numpy_func(self):
        x = [1, 2] * self.ureg.m
        y = [0, 50, 100] * self.ureg.mm
        xx, yy = np.meshgrid(x, y)
        self.assertQuantityEqual(xx, [[1, 2], [1, 2], [1, 2]] * self.ureg.m)
        self.assertQuantityEqual(yy, [[0, 0], [50, 50], [100, 100]] * self.ureg.mm)

    @helpers.requires_array_function_protocol()
    def test_isclose_numpy_func(self):
        q2 = [[1000.05, 2000], [3000.00007, 4001]] * self.ureg.mm
        self.assertNDArrayEqual(
            np.isclose(self.q, q2), np.array([[False, True], [True, False]])
        )
        self.assertNDArrayEqual(
            np.isclose(self.q, q2, atol=1e-5, rtol=1e-7),
            np.array([[False, True], [True, False]]),
        )

    @helpers.requires_array_function_protocol()
    def test_interp_numpy_func(self):
        x = [1, 4] * self.ureg.m
        xp = np.linspace(0, 3, 5) * self.ureg.m
        fp = self.Q_([0, 5, 10, 15, 20], self.ureg.degC)
        self.assertQuantityAlmostEqual(
            np.interp(x, xp, fp), self.Q_([6.66667, 20.0], self.ureg.degC), rtol=1e-5
        )

        x_ = np.array([1, 4])
        xp_ = np.linspace(0, 3, 5)
        fp_ = [0, 5, 10, 15, 20]

        self.assertQuantityAlmostEqual(
            np.interp(x_, xp_, fp), self.Q_([6.6667, 20.0], self.ureg.degC), rtol=1e-5
        )
        self.assertQuantityAlmostEqual(np.interp(x, xp, fp_), [6.6667, 20.0], rtol=1e-5)

    def test_comparisons(self):
        self.assertNDArrayEqual(
            self.q > 2 * self.ureg.m, np.array([[False, False], [True, True]])
        )
        self.assertNDArrayEqual(
            self.q < 2 * self.ureg.m, np.array([[True, False], [False, False]])
        )

    @helpers.requires_array_function_protocol()
    def test_where(self):
        self.assertQuantityEqual(
            np.where(self.q >= 2 * self.ureg.m, self.q, 20 * self.ureg.m),
            [[20, 2], [3, 4]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 2 * self.ureg.m, self.q, 0),
            [[0, 2], [3, 4]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 2 * self.ureg.m, self.q, np.nan),
            [[np.nan, 2], [3, 4]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 3 * self.ureg.m, 0, self.q),
            [[1, 2], [0, 0]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 3 * self.ureg.m, np.nan, self.q),
            [[1, 2], [np.nan, np.nan]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 2 * self.ureg.m, self.q, np.array(np.nan)),
            [[np.nan, 2], [3, 4]] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.where(self.q >= 3 * self.ureg.m, np.array(np.nan), self.q),
            [[1, 2], [np.nan, np.nan]] * self.ureg.m,
        )
        self.assertRaises(
            DimensionalityError,
            np.where,
            self.q < 2 * self.ureg.m,
            self.q,
            0 * self.ureg.J,
        )

    @helpers.requires_array_function_protocol()
    def test_fabs(self):
        self.assertQuantityEqual(
            np.fabs(self.q - 2 * self.ureg.m), self.Q_([[1, 0], [1, 2]], "m")
        )

    @helpers.requires_array_function_protocol()
    def test_isin(self):
        self.assertNDArrayEqual(
            np.isin(self.q, self.Q_([0, 2, 4], "m")),
            np.array([[False, True], [False, True]]),
        )
        self.assertNDArrayEqual(
            np.isin(self.q, self.Q_([0, 2, 4], "J")),
            np.array([[False, False], [False, False]]),
        )
        self.assertNDArrayEqual(
            np.isin(self.q, [self.Q_(2, "m"), self.Q_(4, "J")]),
            np.array([[False, True], [False, False]]),
        )
        self.assertNDArrayEqual(
            np.isin(self.q, self.q.m), np.array([[False, False], [False, False]])
        )
        self.assertNDArrayEqual(
            np.isin(self.q / self.ureg.cm, [1, 3]),
            np.array([[True, False], [True, False]]),
        )
        self.assertRaises(ValueError, np.isin, self.q.m, self.q)

    @helpers.requires_array_function_protocol()
    def test_percentile(self):
        self.assertQuantityEqual(np.percentile(self.q, 25), self.Q_(1.75, "m"))

    @helpers.requires_array_function_protocol()
    def test_nanpercentile(self):
        self.assertQuantityEqual(np.nanpercentile(self.q_nan, 25), self.Q_(1.5, "m"))

    @helpers.requires_array_function_protocol()
    def test_quantile(self):
        self.assertQuantityEqual(np.quantile(self.q, 0.25), self.Q_(1.75, "m"))

    @helpers.requires_array_function_protocol()
    def test_nanquantile(self):
        self.assertQuantityEqual(np.nanquantile(self.q_nan, 0.25), self.Q_(1.5, "m"))

    @helpers.requires_array_function_protocol()
    def test_copyto(self):
        a = self.q.m
        q = copy.copy(self.q)
        np.copyto(q, 2 * q, where=[True, False])
        self.assertQuantityEqual(q, self.Q_([[2, 2], [6, 4]], "m"))
        np.copyto(q, 0, where=[[False, False], [True, False]])
        self.assertQuantityEqual(q, self.Q_([[2, 2], [0, 4]], "m"))
        np.copyto(a, q)
        self.assertNDArrayEqual(a, np.array([[2, 2], [0, 4]]))

    @helpers.requires_array_function_protocol()
    def test_tile(self):
        self.assertQuantityEqual(
            np.tile(self.q, 2), np.array([[1, 2, 1, 2], [3, 4, 3, 4]]) * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_rot90(self):
        self.assertQuantityEqual(
            np.rot90(self.q), np.array([[2, 4], [1, 3]]) * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_insert(self):
        self.assertQuantityEqual(
            np.insert(self.q, 1, 0 * self.ureg.m, axis=1),
            np.array([[1, 0, 2], [3, 0, 4]]) * self.ureg.m,
        )

    def test_ndarray_downcast(self):
        with self.assertWarns(UnitStrippedWarning):
            np.asarray(self.q)

    def test_ndarray_downcast_with_dtype(self):
        with self.assertWarns(UnitStrippedWarning):
            qarr = np.asarray(self.q, dtype=np.float64)
            self.assertEqual(qarr.dtype, np.float64)

    def test_array_protocol_unavailable(self):
        for attr in ("__array_struct__", "__array_interface__"):
            self.assertRaises(AttributeError, getattr, self.q, attr)

    @helpers.requires_array_function_protocol()
    def test_resize(self):
        self.assertQuantityEqual(
            np.resize(self.q, (2, 4)), [[1, 2, 3, 4], [1, 2, 3, 4]] * self.ureg.m
        )

    @helpers.requires_array_function_protocol()
    def test_pad(self):
        # Tests reproduced with modification from NumPy documentation
        a = [1, 2, 3, 4, 5] * self.ureg.m
        b = self.Q_([4.0, 6.0, 8.0, 9.0, -3.0], "degC")

        self.assertQuantityEqual(
            np.pad(a, (2, 3), "constant"), [0, 0, 1, 2, 3, 4, 5, 0, 0, 0] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "constant", constant_values=(0, 600 * self.ureg.cm)),
            [0, 0, 1, 2, 3, 4, 5, 6, 6, 6] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(
                b, (2, 1), "constant", constant_values=(np.nan, self.Q_(10, "degC"))
            ),
            self.Q_([np.nan, np.nan, 4, 6, 8, 9, -3, 10], "degC"),
        )
        self.assertRaises(
            DimensionalityError, np.pad, a, (2, 3), "constant", constant_values=4
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "edge"), [1, 1, 1, 2, 3, 4, 5, 5, 5, 5] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "linear_ramp"),
            [0, 0, 1, 2, 3, 4, 5, 3, 1, 0] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "linear_ramp", end_values=(5, -4) * self.ureg.m),
            [5, 3, 1, 2, 3, 4, 5, 2, -1, -4] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(a, (2,), "maximum"), [5, 5, 1, 2, 3, 4, 5, 5, 5] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2,), "mean"), [3, 3, 1, 2, 3, 4, 5, 3, 3] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2,), "median"), [3, 3, 1, 2, 3, 4, 5, 3, 3] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(self.q, ((3, 2), (2, 3)), "minimum"),
            [
                [1, 1, 1, 2, 1, 1, 1],
                [1, 1, 1, 2, 1, 1, 1],
                [1, 1, 1, 2, 1, 1, 1],
                [1, 1, 1, 2, 1, 1, 1],
                [3, 3, 3, 4, 3, 3, 3],
                [1, 1, 1, 2, 1, 1, 1],
                [1, 1, 1, 2, 1, 1, 1],
            ]
            * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "reflect"), [3, 2, 1, 2, 3, 4, 5, 4, 3, 2] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "reflect", reflect_type="odd"),
            [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "symmetric"), [2, 1, 1, 2, 3, 4, 5, 5, 4, 3] * self.ureg.m
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "symmetric", reflect_type="odd"),
            [0, 1, 1, 2, 3, 4, 5, 5, 6, 7] * self.ureg.m,
        )
        self.assertQuantityEqual(
            np.pad(a, (2, 3), "wrap"), [4, 5, 1, 2, 3, 4, 5, 1, 2, 3] * self.ureg.m
        )

        def pad_with(vector, pad_width, iaxis, kwargs):
            pad_value = kwargs.get("padder", 10)
            vector[: pad_width[0]] = pad_value
            vector[-pad_width[1] :] = pad_value

        b = self.Q_(np.arange(6).reshape((2, 3)), "degC")
        self.assertQuantityEqual(
            np.pad(b, 2, pad_with),
            self.Q_(
                [
                    [10, 10, 10, 10, 10, 10, 10],
                    [10, 10, 10, 10, 10, 10, 10],
                    [10, 10, 0, 1, 2, 10, 10],
                    [10, 10, 3, 4, 5, 10, 10],
                    [10, 10, 10, 10, 10, 10, 10],
                    [10, 10, 10, 10, 10, 10, 10],
                ],
                "degC",
            ),
        )
        self.assertQuantityEqual(
            np.pad(b, 2, pad_with, padder=100),
            self.Q_(
                [
                    [100, 100, 100, 100, 100, 100, 100],
                    [100, 100, 100, 100, 100, 100, 100],
                    [100, 100, 0, 1, 2, 100, 100],
                    [100, 100, 3, 4, 5, 100, 100],
                    [100, 100, 100, 100, 100, 100, 100],
                    [100, 100, 100, 100, 100, 100, 100],
                ],
                "degC",
            ),
        )  # Note: Does not support Quantity pad_with vectorized callable use

    @helpers.requires_array_function_protocol()
    def test_allclose(self):
        self.assertTrue(
            np.allclose([1e10, 1e-8] * self.ureg.m, [1.00001e10, 1e-9] * self.ureg.m)
        )
        self.assertFalse(
            np.allclose([1e10, 1e-8] * self.ureg.m, [1.00001e10, 1e-9] * self.ureg.mm)
        )

    @helpers.requires_array_function_protocol()
    def test_intersect1d(self):
        self.assertQuantityEqual(
            np.intersect1d([1, 3, 4, 3] * self.ureg.m, [3, 1, 2, 1] * self.ureg.m),
            [1, 3] * self.ureg.m,
        )


@unittest.skip
class TestBitTwiddlingUfuncs(TestUFuncs):
    """Universal functions (ufuncs) >  Bittwiddling functions

    http://docs.scipy.org/doc/numpy/reference/ufuncs.html#bittwiddlingfunctions

    bitwise_and(x1, x2[, out])         Compute the bitwise AND of two arrays elementwise.
    bitwise_or(x1, x2[, out])  Compute the bitwise OR of two arrays elementwise.
    bitwise_xor(x1, x2[, out])         Compute the bitwise XOR of two arrays elementwise.
    invert(x[, out])   Compute bitwise inversion, or bitwise NOT, elementwise.
    left_shift(x1, x2[, out])  Shift the bits of an integer to the left.
    right_shift(x1, x2[, out])         Shift the bits of an integer to the right.

    Parameters
    ----------

    Returns
    -------

    """

    @property
    def qless(self):
        return np.asarray([1, 2, 3, 4], dtype=np.uint8) * self.ureg.dimensionless

    @property
    def qs(self):
        return 8 * self.ureg.J

    @property
    def q1(self):
        return np.asarray([1, 2, 3, 4], dtype=np.uint8) * self.ureg.J

    @property
    def q2(self):
        return 2 * self.q1

    @property
    def qm(self):
        return np.asarray([1, 2, 3, 4], dtype=np.uint8) * self.ureg.m

    def test_bitwise_and(self):
        self._test2(np.bitwise_and, self.q1, (self.q2, self.qs), (self.qm,), "same")

    def test_bitwise_or(self):
        self._test2(
            np.bitwise_or, self.q1, (self.q1, self.q2, self.qs), (self.qm,), "same"
        )

    def test_bitwise_xor(self):
        self._test2(
            np.bitwise_xor, self.q1, (self.q1, self.q2, self.qs), (self.qm,), "same"
        )

    def test_invert(self):
        self._test1(np.invert, (self.q1, self.q2, self.qs), (), "same")

    def test_left_shift(self):
        self._test2(
            np.left_shift, self.q1, (self.qless, 2), (self.q1, self.q2, self.qs), "same"
        )

    def test_right_shift(self):
        self._test2(
            np.right_shift,
            self.q1,
            (self.qless, 2),
            (self.q1, self.q2, self.qs),
            "same",
        )
