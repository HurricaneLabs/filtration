import random
import unittest

from nose2.tools import params
from pyparsing import ParseException


symbol_tests = [
    "symbol",
    "_symbol",
    "symbol.symbol",
    "_symbol.symbol",
    ("'value'", ParseException),
    ('"value"', ParseException),
    ("123", ParseException),
]

value_tests = [
    "'value'",
    '"value"',
    "123",
    ("symbol", ParseException),
    ("_symbol", ParseException),
    ("symbol.symbol", ParseException),
    ("_symbol.symbol", ParseException),
]

regex_tests = [
    "/regex/",
    ("/not[a-valid/", ParseException),
    ("/not(a-valid/", ParseException),
    ("/not-a-valid)", ParseException),
    ("'regex'", ParseException),
]

subnet_tests = [
    "0.0.0.0/0",
    "0.0.0.0/8",
    "172.16.0.0/8",
    "192.168.0.0/16",
    "192.168.100.0/24",
    "255.255.255.255/32",
    ("0.0.0.0", ParseException),
    ("0.0.0.0/33", ParseException),
    ("256.256.256.256/0", ParseException),
    ("256.256.256.256/32", ParseException),
]

term_parse_tests = [
    "symbol1",
    "symbol1 == symbol2",
    "symbol1 == 'value1'",
    "symbol1 =~ /regex1/",
    "symbol1 in 10.0.0.0/8",
    "symbol1 in 'list','list','list'",
    "symbol1 in symbol1",
    "'value1' in symbol1",
]

expression_parse_tests = [
    "{0}",
    "not {0}",
    "({0})",
    "not ({0})",
    "{0} and {1}",
    "{0} or {1}",
    "{0} and {1} or {2}",
    "{0} and ({1} or {2})",
    "{0} or {1} and {2}",
    "({0} or {1}) and {2}",
]

expression_evaluate_tests = {
    "bare_symbol": ("symbol_true", "symbol_false"),
    "nested_dict": ("dict.symbol_true", "dict.doesnt_exist"),
    "==": ("symbol_int == 1", "symbol_int == 2"),
    "!=": ("symbol_int != 2", "symbol_int != 1"),
    "<": ("symbol_int < 2", "symbol_int < 1"),
    "<=": ("symbol_int <= 1", "symbol_int <= 0"),
    ">": ("symbol_int > 0", "symbol_int > 1"),
    ">=": ("symbol_int >= 1", "symbol_int >= 2"),
    "in": ("symbol_str in 'a','b'", "symbol_str in 'c','d'"),
    "=~": ("symbol_str =~ /^a/", "symbol_str =~ /c$/"),
}

def generate_expression_tests():
    for test_expr_fmt in expression_parse_tests:
        for (expr_a, expr_b, expr_c) in zip(term_parse_tests, term_parse_tests, term_parse_tests):
            yield test_expr_fmt.format(expr_a, expr_b, expr_c)


class TestGrammar(unittest.TestCase):
    @params(*symbol_tests)
    def test_parse_symbol(self, test_expr, expect_failure=None):
        """
            A symbol begins with a letter or an underscore, and may contain any combination of
            letters, numbers, dot (".") and underscore ("_")
        """
        from filtration.grammar import Symbol

        if expect_failure is None:
            Symbol.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Symbol.parseString, test_expr)

    @params(*value_tests)
    def test_parse_value(self, test_expr, expect_failure=None):
        """
            A value is a quoted string, with single or double quotes, or a number.
        """
        from filtration.grammar import Value

        if expect_failure is None:
            Value.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Value.parseString, test_expr)

    @params(*regex_tests)
    def test_parse_regex(self, test_expr, expect_failure=None):
        """
            A regex is a string surrounded by /
        """
        from filtration.grammar import Regex

        if expect_failure is None:
            Regex.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Regex.parseString, test_expr)

    @params(*subnet_tests)
    def test_parse_subnet(self, test_expr, expect_failure=None):
        """
            Subnets are defined in CIDR notation
        """
        from filtration.grammar import Subnet

        if expect_failure is None:
            Subnet.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Subnet.parseString, test_expr)

    @params(*range(1, 10))
    def test_parse_valuelist(self, test_expr_len, expect_failure=None):
        """
            A list is two or more values, separated by commas
        """
        from filtration.grammar import List

        test_expr = ",".join(["'value'" for _ in range(0, test_expr_len)])
        if test_expr_len > 1:
            List.parseString(test_expr)
        else:
            self.assertRaises(ParseException, List.parseString, test_expr)

    @params(*term_parse_tests)
    def test_parse_expression(self, test_expr, expect_failure=None):
        """
        """
        from filtration.grammar import Statement

        Statement.parseString(test_expr)

    @params(*generate_expression_tests())
    def test_parse_filter(self, test_expr):
        """
        """
        from filtration.grammar import Expression

        Expression.parseString(test_expr)

    def test_evaluate_symbol(self):
        """
        """
        from filtration.tokens import Symbol

        sym = Symbol.parseString("symbol")
        assert sym({"symbol": "value"}) == "value"

    def test_evaluate_value(self):
        """
        """
        from filtration.tokens import Value

        val = Value.parseString("'value'")
        assert val({}) == "value"

    def test_evaluate_regex(self):
        """
        """
        import re
        from filtration.tokens import Regex

        rex = Regex.parseString("/abc/")
        assert rex({}) == re.compile("abc")

    def test_evaluate_subnet(self):
        """
        """
        import ipcalc
        from filtration.tokens import Subnet

        subnet = Subnet.parseString("192.168.0.0/16")
        assert subnet({}).network() == "192.168.0.0" and subnet({}).size() == 65536

    @params(*expression_evaluate_tests.values())
    def test_evaluate_expression(self, test_expr_true, test_expr_false=None):
        """
        """
        from filtration import Expression

        context = {
            "symbol_true": True,
            "symbol_False": False,
            "symbol_int": 1,
            "symbol_str": "a",
        }
        context["dict"] = context

        expr = Expression.parseString(test_expr_true)
        assert expr(context)

        expr = Expression.parseString(test_expr_false)
        self.assertFalse(expr(context))

    @params(*expression_evaluate_tests.values())
    def test_evaluate_not_expression(self, test_expr_true, test_expr_false=None):
        """
        """
        from filtration import Expression

        context = {
            "symbol_true": True,
            "symbol_False": False,
            "symbol_int": 1,
            "symbol_str": "a",
        }
        context["dict"] = context

        expr = Expression.parseString("not {0}".format(test_expr_true))
        self.assertFalse(expr(context))

        expr = Expression.parseString("not {0}".format(test_expr_false))
        assert expr(context)

    @params(*expression_evaluate_tests.values())
    def test_evaluate_and_expression(self, test_expr_true, test_expr_false=None):
        """
        """
        from filtration import Expression

        context = {
            "symbol_true": True,
            "symbol_False": False,
            "symbol_int": 1,
            "symbol_str": "a",
        }
        context["dict"] = context

        test_expr = "{0} and {1}".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertFalse(expr(context))

        test_expr = "not({0} and {1})".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertTrue(expr(context))

        test_expr = "{0} and not {1}".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertTrue(expr(context))

        test_expr = "not {0} and {1}".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertFalse(expr(context))

        test_expr = "{0} or {1}".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertTrue(expr(context))

        test_expr = "not({0} or {1})".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertFalse(expr(context))
