import unittest

from nose2.tools import params
from pyparsing import ParseException
import fauxfactory


symbol_tests = [
    fauxfactory.gen_alpha(),
    "_{0}".format(fauxfactory.gen_alpha()),
    "{0}.{1}".format(fauxfactory.gen_alpha(), fauxfactory.gen_alpha()),
    "_{0}.{1}".format(fauxfactory.gen_alpha(), fauxfactory.gen_alpha()),
    ("'{0}'".format(fauxfactory.gen_alpha()), ParseException),
    ('"{0}"'.format(fauxfactory.gen_alpha()), ParseException),
    (fauxfactory.gen_numeric_string(), ParseException),
]

value_tests = [
    "'{0}'".format(fauxfactory.gen_alpha()),
    '"{0}"'.format(fauxfactory.gen_alpha()),
    fauxfactory.gen_numeric_string(),
    fauxfactory.gen_date().isoformat(),
    fauxfactory.gen_time().isoformat(),
    fauxfactory.gen_datetime().isoformat(),
    (fauxfactory.gen_alpha(), ParseException),
    ("_{0}".format(fauxfactory.gen_alpha()), ParseException),
    ("{0}.{1}".format(fauxfactory.gen_alpha(), fauxfactory.gen_alpha()), ParseException),
    ("_{0}.{1}".format(fauxfactory.gen_alpha(), fauxfactory.gen_alpha()), ParseException),
]

regex_tests = [
    "/regex/",
    "/regex/i",
    "/regex/im",
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
