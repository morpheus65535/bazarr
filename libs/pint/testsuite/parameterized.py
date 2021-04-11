# Adds Parameterized tests for Python's unittest module
#
# Code from: parameterizedtestcase, version: 0.1.0
# Homepage: https://github.com/msabramo/python_unittest_parameterized_test_case
# Author: Marc Abramowitz, email: marc@marc-abramowitz.com
# License: MIT
#
# Use like this:
#
#    from parameterizedtestcase import ParameterizedTestCase
#
#    class MyTests(ParameterizedTestCase):
#        @ParameterizedTestCase.parameterize(
#            ("input", "expected_output"),
#            [
#                ("2+4", 6),
#                ("3+5", 8),
#                ("6*9", 54),
#            ]
#        )
#        def test_eval(self, input, expected_output):
#            self.assertEqual(eval(input), expected_output)

import unittest
from collections.abc import Callable
from functools import wraps


def augment_method_docstring(
    method, new_class_dict, classname, param_names, param_values, new_method
):
    param_assignments_str = "; ".join(
        ["%s = %s" % (k, v) for (k, v) in zip(param_names, param_values)]
    )
    extra_doc = "%s (%s.%s) [with %s] " % (
        method.__name__,
        new_class_dict.get("__module__", "<module>"),
        classname,
        param_assignments_str,
    )

    try:
        new_method.__doc__ = extra_doc + new_method.__doc__
    except TypeError:  # Catches when new_method.__doc__ is None
        new_method.__doc__ = extra_doc


class ParameterizedTestCaseMetaClass(type):
    method_counter = {}

    def __new__(meta, classname, bases, class_dict):
        new_class_dict = {}

        for attr_name, attr_value in list(class_dict.items()):
            if isinstance(attr_value, Callable) and hasattr(attr_value, "param_names"):
                # print("Processing attr_name = %r; attr_value = %r" % (
                #     attr_name, attr_value))

                method = attr_value
                param_names = attr_value.param_names
                data = attr_value.data
                func_name_format = attr_value.func_name_format

                meta.process_method(
                    classname,
                    method,
                    param_names,
                    data,
                    new_class_dict,
                    func_name_format,
                )
            else:
                new_class_dict[attr_name] = attr_value

        return type.__new__(meta, classname, bases, new_class_dict)

    @classmethod
    def process_method(
        cls, classname, method, param_names, data, new_class_dict, func_name_format
    ):
        method_counter = cls.method_counter

        for param_values in data:
            new_method = cls.new_method(method, param_values)
            method_counter[method.__name__] = method_counter.get(method.__name__, 0) + 1
            case_data = dict(list(zip(param_names, param_values)))
            case_data["func_name"] = method.__name__
            case_data["case_num"] = method_counter[method.__name__]

            new_method.__name__ = func_name_format.format(**case_data)

            augment_method_docstring(
                method, new_class_dict, classname, param_names, param_values, new_method
            )
            new_class_dict[new_method.__name__] = new_method

    @classmethod
    def new_method(cls, method, param_values):
        @wraps(method)
        def new_method(self):
            return method(self, *param_values)

        return new_method


class ParameterizedTestMixin(metaclass=ParameterizedTestCaseMetaClass):
    @classmethod
    def parameterize(
        cls, param_names, data, func_name_format="{func_name}_{case_num:05d}"
    ):
        """Decorator for parameterizing a test method - example:

        @ParameterizedTestCase.parameterize(
            ("isbn", "expected_title"), [
                ("0262033844", "Introduction to Algorithms"),
                ("0321558146", "Campbell Essential Biology")])

        Parameters
        ----------
        param_names :

        data :

        func_name_format :
             (Default value = "{func_name}_{case_num:05d}")

        Returns
        -------

        """

        def decorator(func):
            @wraps(func)
            def newfunc(*arg, **kwargs):
                return func(*arg, **kwargs)

            newfunc.param_names = param_names
            newfunc.data = data
            newfunc.func_name_format = func_name_format

            return newfunc

        return decorator


class ParameterizedTestCase(unittest.TestCase, ParameterizedTestMixin):
    pass
