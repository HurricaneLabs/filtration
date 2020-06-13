import unittest

from nose2.tools import params


import re
regex_evaluate_tests = [
    ("/abc/", re.compile("abc")),
    ("/abc/i", re.compile("abc", flags=re.I)),
    ("/abc/m", re.compile("abc", flags=re.M)),
    ("/abc/s", re.compile("abc", flags=re.S)),
    ("/abc/ims", re.compile("abc", flags=re.I | re.M | re.S)),
]

expression_evaluate_tests = [
    ("symbol_true", "symbol_false"),
    ("symbol_true and symbol_true", "symbol_true and symbol_false"),
    ("symbol_true or symbol_false", "symbol_false or symbol_false"),
    ("not symbol_false", "not symbol_true"),
    ("dict.symbol_true", "dict.doesnt_exist"),
    ("symbol_int == 1", "symbol_int == 2"),
    ("symbol_int != 2", "symbol_int != 1"),
    ("symbol_int < 2", "symbol_int < 1"),
    ("symbol_int <= 1", "symbol_int <= 0"),
    ("symbol_int > 0", "symbol_int > 1"),
    ("symbol_int >= 1", "symbol_int >= 2"),
    ("symbol_str in 'a','b'", "symbol_str in 'c','d'"),
    (None, "'a' in nonexistant"),
    ("symbol_str =~ /^a/", "symbol_str =~ /c$/"),
    ("symbol_list =~ /cde/", "symbol_list =~ /xyz/"),
    (None, "nonexistant =~ /a/"),
    ("symbol_dt > 2015-03-01", "symbol_dt < 2000-01-01"),
]


class TestTokens(unittest.TestCase):
    def test_evaluate_symbol(self):
        """
        """
        from filtration import Symbol

        sym = Symbol.parseString("symbol")[0]
        self.assertEqual(sym({"symbol": "value"}), "value")

    def test_evaluate_value(self):
        """
        """
        from filtration import Value

        val = Value.parseString("'value'")[0]
        self.assertEqual(val({}), "value")

    @params(*regex_evaluate_tests)
    def test_evaluate_regex(self, test_expr, expected):
        """
        """
        from filtration import Regex

        rex = Regex.parseString(test_expr)[0]
        result = rex({})

        self.assertEqual(result.pattern, expected.pattern)
        self.assertEqual(result.flags, expected.flags)

    def test_evaluate_subnet(self):
        """
        """
        from filtration import Subnet

        subnet = Subnet.parseString("192.168.0.0/16")[0]
        self.assertEqual(subnet({}).network(), "192.168.0.0")
        self.assertEqual(subnet({}).size(), 2 ** 16)

    @params(*expression_evaluate_tests)
    def test_evaluate_expression(self, test_expr_true, test_expr_false=None):
        """
        """
        import datetime
        from filtration import Expression

        context = {
            "symbol_true": True,
            "symbol_False": False,
            "symbol_int": 1,
            "symbol_str": "a",
            "symbol_dt": datetime.datetime.now(),
            "symbol_list": ["abcde", "cdefg"]
        }
        context["dict"] = context

        if test_expr_true:
            expr = Expression.parseString(test_expr_true)
            self.assertTrue(expr(context))

        if test_expr_false:
            expr = Expression.parseString(test_expr_false)
            self.assertFalse(expr(context))

    def test_subnet_contains(self):
        """
        """
        from filtration import Expression

        expr = Expression.parseString("src in 127.0.0.0/8")
        self.assertTrue(expr({"src": "127.0.0.1"}))
        self.assertFalse(expr({"src": "localhost"}))
