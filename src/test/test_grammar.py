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
        from filtration import Symbol

        if expect_failure is None:
            Symbol.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Symbol.parseString, test_expr)

    @params(*value_tests)
    def test_parse_value(self, test_expr, expect_failure=None):
        """
            A value is a quoted string, with single or double quotes, or a number.
        """
        from filtration import Value

        if expect_failure is None:
            Value.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Value.parseString, test_expr)

    @params(*regex_tests)
    def test_parse_regex(self, test_expr, expect_failure=None):
        """
            A regex is a string surrounded by /
        """
        from filtration import Regex

        if expect_failure is None:
            Regex.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Regex.parseString, test_expr)

    @params(*subnet_tests)
    def test_parse_subnet(self, test_expr, expect_failure=None):
        """
            Subnets are defined in CIDR notation
        """
        from filtration import Subnet

        if expect_failure is None:
            Subnet.parseString(test_expr)
        else:
            self.assertRaises(expect_failure, Subnet.parseString, test_expr)

    @params(*range(1, 10))
    def test_parse_valuelist(self, test_expr_len, expect_failure=None):
        """
            A list is two or more values, separated by commas
        """
        from filtration import List

        test_expr = ",".join(["'value'" for _ in range(0, test_expr_len)])
        if test_expr_len > 1:
            List.parseString(test_expr)
        else:
            self.assertRaises(ParseException, List.parseString, test_expr)

    @params(*term_parse_tests)
    def test_parse_expression(self, test_expr, expect_failure=None):
        """
        """
        from filtration import Expression

        Expression.parseString(test_expr)

    @params(*generate_expression_tests())
    def test_parse_filter(self, test_expr):
        """
        """
        from filtration import Filter

        Filter.parseString(test_expr)

    def test_evaluate_symbol(self):
        """
        """
        from filtration import Symbol

        sym = Symbol.parseString("symbol")
        assert sym({"symbol": "value"}) == "value"

    def test_evaluate_value(self):
        """
        """
        from filtration import Value

        val = Value.parseString("'value'")
        assert val({}) == "value"

    def test_evaluate_regex(self):
        """
        """
        import re
        from filtration import Regex

        rex = Regex.parseString("/abc/")
        assert rex({}) == re.compile("abc")

    def test_evaluate_subnet(self):
        """
        """
        import ipcalc
        from filtration import Subnet

        subnet = Subnet.parseString("192.168.0.0/16")
        assert subnet({}).network() == "192.168.0.0" and subnet({}).size() == 65536
