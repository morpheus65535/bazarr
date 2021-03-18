import unittest

from pint.compat import tokenizer
from pint.pint_eval import build_eval_tree


class TestPintEval(unittest.TestCase):
    def _test_one(self, input_text, parsed):
        self.assertEqual(build_eval_tree(tokenizer(input_text)).to_string(), parsed)

    def test_build_eval_tree(self):
        self._test_one("3", "3")
        self._test_one("1 + 2", "(1 + 2)")
        # order of operations
        self._test_one("2 * 3 + 4", "((2 * 3) + 4)")
        # parentheses
        self._test_one("2 * (3 + 4)", "(2 * (3 + 4))")
        # more order of operations
        self._test_one("1 + 2 * 3 ** (4 + 3 / 5)", "(1 + (2 * (3 ** (4 + (3 / 5)))))")
        # nested parentheses at beginning
        self._test_one("1 * ((3 + 4) * 5)", "(1 * ((3 + 4) * 5))")
        # nested parentheses at end
        self._test_one("1 * (5 * (3 + 4))", "(1 * (5 * (3 + 4)))")
        # nested parentheses in middle
        self._test_one("1 * (5 * (3 + 4) / 6)", "(1 * ((5 * (3 + 4)) / 6))")
        # unary
        self._test_one("-1", "(- 1)")
        # unary
        self._test_one("3 * -1", "(3 * (- 1))")
        # double unary
        self._test_one("3 * --1", "(3 * (- (- 1)))")
        # parenthetical unary
        self._test_one("3 * -(2 + 4)", "(3 * (- (2 + 4)))")
        # parenthetical unary
        self._test_one("3 * -((2 + 4))", "(3 * (- (2 + 4)))")
        # implicit op
        self._test_one("3 4", "(3 4)")
        # implicit op, then parentheses
        self._test_one("3 (2 + 4)", "(3 (2 + 4))")
        # parentheses, then implicit
        self._test_one("(3 ** 4 ) 5", "((3 ** 4) 5)")
        # implicit op, then exponentiation
        self._test_one("3 4 ** 5", "(3 (4 ** 5))")
        # implicit op, then addition
        self._test_one("3 4 + 5", "((3 4) + 5)")
        # power followed by implicit
        self._test_one("3 ** 4 5", "((3 ** 4) 5)")
        # implicit with parentheses
        self._test_one("3 (4 ** 5)", "(3 (4 ** 5))")
        # exponent with e
        self._test_one("3e-1", "3e-1")
        # multiple units with exponents
        self._test_one("kg ** 1 * s ** 2", "((kg ** 1) * (s ** 2))")
        # multiple units with neg exponents
        self._test_one("kg ** -1 * s ** -2", "((kg ** (- 1)) * (s ** (- 2)))")
        # multiple units with neg exponents
        self._test_one("kg^-1 * s^-2", "((kg ^ (- 1)) * (s ^ (- 2)))")
        # multiple units with neg exponents, implicit op
        self._test_one("kg^-1 s^-2", "((kg ^ (- 1)) (s ^ (- 2)))")
        # nested power
        self._test_one("2 ^ 3 ^ 2", "(2 ^ (3 ^ 2))")
        # nested power
        self._test_one("gram * second / meter ** 2", "((gram * second) / (meter ** 2))")
        # nested power
        self._test_one("gram / meter ** 2 / second", "((gram / (meter ** 2)) / second)")
        # units should behave like numbers, so we don't need a bunch of extra tests for them
        # implicit op, then addition
        self._test_one("3 kg + 5", "((3 kg) + 5)")
