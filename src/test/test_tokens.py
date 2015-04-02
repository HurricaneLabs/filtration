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
    ("dict.symbol_true", "dict.doesnt_exist"),
    ("symbol_int == 1", "symbol_int == 2"),
    ("symbol_int != 2", "symbol_int != 1"),
    ("symbol_int < 2", "symbol_int < 1"),
    ("symbol_int <= 1", "symbol_int <= 0"),
    ("symbol_int > 0", "symbol_int > 1"),
    ("symbol_int >= 1", "symbol_int >= 2"),
    ("symbol_str in 'a','b'", "symbol_str in 'c','d'"),
    ("symbol_str =~ /^a/", "symbol_str =~ /c$/"),
    ("symbol_dt > 2015-03-01", "symbol_dt < 2000-01-01"),
]

expression_repr_tests = [
    ("symbol_true", "symbol_true"),
    ("dict.symbol_true", "dict.symbol_true"),
    ("symbol_int == 1", "symbol_int == 1"),
    ("symbol_int != 2", "symbol_int != 2"),
    ("symbol_int < 2", "symbol_int < 2"),
    ("symbol_int <= 1", "symbol_int <= 1"),
    ("symbol_int > 0", "symbol_int > 0"),
    ("symbol_int >= 1", "symbol_int >= 1"),
    ("symbol_str in 'a','b'", "symbol_str in ['a', 'b']"),
    ("symbol_str =~ /^a/", "symbol_str =~ /^a/"),
]


class TestTokens(unittest.TestCase):
    def test_evaluate_symbol(self):
        """
        """
        from filtration.tokens import Symbol

        sym = Symbol.parseString("symbol")
        assert sym({"symbol": "value"}) == "value"

    def test_repr_symbol(self):
        """
        """
        from filtration.tokens import Symbol

        sym = Symbol.parseString("symbol")
        assert repr(sym) == "symbol"

    def test_evaluate_value(self):
        """
        """
        from filtration.tokens import Value

        val = Value.parseString("'value'")
        assert val({}) == "value"

    def test_repr_value(self):
        """
        """
        from filtration.tokens import Value

        val = Value.parseString("'value'")
        assert repr(val) == "'value'"

    @params(*regex_evaluate_tests)
    def test_evaluate_regex(self, test_expr, expected):
        """
        """
        from filtration.tokens import Regex

        rex = Regex.parseString(test_expr)
        self.assertEqual(rex({}), expected)

    @params(*[test[0] for test in regex_evaluate_tests])
    def test_repr_regex(self, test_expr):
        """
        """
        from filtration.tokens import Regex

        rex = Regex.parseString(test_expr)
        self.assertEqual(repr(rex), test_expr)

    def test_evaluate_subnet(self):
        """
        """
        from filtration.tokens import Subnet

        subnet = Subnet.parseString("192.168.0.0/16")
        assert subnet({}).network() == "192.168.0.0" and subnet({}).size() == 2 ** 16

    def test_repr_subnet(self):
        """
        """
        from filtration.tokens import Subnet

        subnet = Subnet.parseString("192.168.0.0/16")
        assert repr(subnet) == "192.168.0.0/16"

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
        }
        context["dict"] = context

        expr = Expression.parseString(test_expr_true)
        assert expr(context)

        expr = Expression.parseString(test_expr_false)
        self.assertFalse(expr(context))

    @params(*expression_repr_tests)
    def test_repr_expression(self, test_expr, test_expr_repr):
        """
        """
        from filtration import Expression

        expr = Expression.parseString(test_expr)
        self.assertEqual(repr(expr), test_expr_repr)

    @params(*expression_evaluate_tests)
    def test_evaluate_not_expression(self, test_expr_true, test_expr_false=None):
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
        }
        context["dict"] = context

        expr = Expression.parseString("not {0}".format(test_expr_true))
        self.assertFalse(expr(context))

        expr = Expression.parseString("not {0}".format(test_expr_false))
        assert expr(context)

    @params(*expression_repr_tests)
    def test_repr_not_expression(self, test_expr, test_expr_repr):
        """
        """
        from filtration import Expression

        expr = Expression.parseString("not {0}".format(test_expr))
        self.assertEqual(repr(expr), "not {0}".format(test_expr_repr))

    @params(*expression_evaluate_tests)
    def test_evaluate_and_expression(self, test_expr_true, test_expr_false=None):
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

    @params(*expression_repr_tests)
    def test_repr_and_expression(self, test_expr, test_expr_repr):
        """
        """
        from filtration import Expression

        expr = Expression.parseString("{0} and {0}".format(test_expr))
        self.assertEqual(repr(expr), "({0} and {0})".format(test_expr_repr))

        expr = Expression.parseString("not({0} and {0})".format(test_expr))
        self.assertEqual(repr(expr), "not ({0} and {0})".format(test_expr_repr))

        expr = Expression.parseString("{0} and not {0}".format(test_expr))
        self.assertEqual(repr(expr), "({0} and not {0})".format(test_expr_repr))

        expr = Expression.parseString("not {0} and {0}".format(test_expr))
        self.assertEqual(repr(expr), "(not {0} and {0})".format(test_expr_repr))

    @params(*expression_evaluate_tests)
    def test_evaluate_or_expression(self, test_expr_true, test_expr_false=None):
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
        }
        context["dict"] = context


        test_expr = "{0} or {1}".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertTrue(expr(context))

        test_expr = "not({0} or {1})".format(test_expr_true, test_expr_false)
        expr = Expression.parseString(test_expr)
        self.assertFalse(expr(context))

    @params(*expression_repr_tests)
    def test_repr_or_expression(self, test_expr, test_expr_repr):
        """
        """
        from filtration import Expression

        expr = Expression.parseString("{0} or {0}".format(test_expr))
        self.assertEqual(repr(expr), "({0} or {0})".format(test_expr_repr))

        expr = Expression.parseString("not({0} or {0})".format(test_expr))
        self.assertEqual(repr(expr), "not ({0} or {0})".format(test_expr_repr))
