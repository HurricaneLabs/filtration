import unittest

from nose2.tools import params
#from pyparsing import ParseException


qs_parse_tests = [
    # Basic operators
    ("symbol__eq=value", "symbol == 'value'"),
    ("symbol__ne=value", "symbol != 'value'"),
    ("symbol__lt=0", "symbol < 0"),
    ("symbol__le=0", "symbol <= 0"),
    ("symbol__gt=0", "symbol > 0"),
    ("symbol__ge=0", "symbol >= 0"),

    # Regex
    ("symbol__contains=pattern", "symbol =~ /pattern/"),
    ("symbol__icontains=pattern", "symbol =~ /pattern/i"),
    ("symbol__startswith=pattern", "symbol =~ /^pattern/"),
    ("symbol__istartswith=pattern", "symbol =~ /^pattern/i"),
    ("symbol__endswith=pattern", "symbol =~ /pattern$/"),
    ("symbol__iendswith=pattern", "symbol =~ /pattern$/i"),

    # Dictionary expansion
    ("symbol__key__eq=value", "symbol.key == 'value'"),
]


class TestQsParser(unittest.TestCase):
    @params(*qs_parse_tests)
    def test_qs_parse(self, qs_test_expr, test_expr):
        from filtration import Expression

        qs_expr = Expression.parseQsString(qs_test_expr)
        expr = Expression.parseString(test_expr)

        self.assertEqual(repr(qs_expr), repr(expr))
