import pytest
from pyparsing import ParseException

from filtration import Expression, List, Regex, Statement, Subnet, Symbol, Value

SYMBOLS = ["abcXYZ", "_abcXYZ", "abc.XYZ", "_abc.XYZ"]
NOT_SYMBOLS = ["'abcXYZ'", '"abcXYZ"', "12345"]

VALUES = [
    "'abcXYZ'",
    '"abcXYZ"',
    "12345",
    "2015-03-01",
    "12:34:56",
    "2015-03-01T12:34:56",
]
NOT_VALUES = ["abcXYZ", "_abcXYZ", "abc.XYZ", "_abc.XYZ"]

REGEXES = ["/regex/", "/regex/i", "/regex/im"]
NOT_REGEXES = ["/not[a-valid/", "/not(a-valid/", "/not-a-valid)", "'regex'"]

SUBNETS = [
    "0.0.0.0/0",
    "0.0.0.0/8",
    "172.16.0.0/8",
    "192.168.0.0/16",
    "192.168.100.0/24",
    "255.255.255.255/32",
]
NOT_SUBNETS = ["0.0.0.0", "0.0.0.0/33", "256.256.256.256/0", "256.256.256.256/32"]

TERMS = [
    "symbol1",
    "symbol1 == symbol2",
    "symbol1 == 'value1'",
    "symbol1 =~ /regex1/",
    "symbol1 in 10.0.0.0/8",
    "symbol1 in 'list','list','list'",
    "symbol1 in symbol1",
    "'value1' in symbol1",
]

EXPRESSION_FORMATS = [
    "{0}",
    "not {0}",
    "({0})",
    "not ({0})",
    "{0} and {0}",
    "{0} or {0}",
    "{0} and {0} or {0}",
    "{0} and ({0} or {0})",
    "{0} or {0} and {0}",
    "({0} or {0}) and {0}",
]


@pytest.mark.parametrize("expr", SYMBOLS)
def test_parse_symbol(expr: str) -> None:
    """A symbol starts with a letter or underscore, then letters, digits, dots or underscores."""
    Symbol.parse_string(expr)


@pytest.mark.parametrize("expr", NOT_SYMBOLS)
def test_parse_symbol_rejects(expr: str) -> None:
    """Quoted strings and bare numbers are not symbols."""
    with pytest.raises(ParseException):
        Symbol.parse_string(expr)


@pytest.mark.parametrize("expr", VALUES)
def test_parse_value(expr: str) -> None:
    """A value is a quoted string, a number, a date, a time or a date/time."""
    Value.parse_string(expr)


@pytest.mark.parametrize("expr", NOT_VALUES)
def test_parse_value_rejects(expr: str) -> None:
    """Bare words are symbols, not values."""
    with pytest.raises(ParseException):
        Value.parse_string(expr)


@pytest.mark.parametrize("expr", REGEXES)
def test_parse_regex(expr: str) -> None:
    """A regex is wrapped in / with optional i, m or s flags after it."""
    Regex.parse_string(expr)


@pytest.mark.parametrize("expr", NOT_REGEXES)
def test_parse_regex_rejects(expr: str) -> None:
    """Invalid patterns and unslashed strings are not regexes."""
    with pytest.raises(ParseException):
        Regex.parse_string(expr)


@pytest.mark.parametrize("expr", SUBNETS)
def test_parse_subnet(expr: str) -> None:
    """Subnets are IPv4 CIDR notation."""
    Subnet.parse_string(expr)


@pytest.mark.parametrize("expr", NOT_SUBNETS)
def test_parse_subnet_rejects(expr: str) -> None:
    """A bare IP, a prefix over 32 or an octet over 255 is not a subnet."""
    with pytest.raises(ParseException):
        Subnet.parse_string(expr)


@pytest.mark.parametrize("length", range(2, 10))
def test_parse_valuelist(length: int) -> None:
    """A list is two or more values separated by commas."""
    List.parse_string(",".join(["'value'"] * length))


def test_parse_valuelist_rejects_single_value() -> None:
    """One value on its own is not a list."""
    with pytest.raises(ParseException):
        List.parse_string("'value'")


@pytest.mark.parametrize("expr", TERMS)
def test_parse_statement(expr: str) -> None:
    """Each statement form parses."""
    Statement.parse_string(expr)


@pytest.mark.parametrize("term", TERMS)
@pytest.mark.parametrize("fmt", EXPRESSION_FORMATS)
def test_parse_expression(fmt: str, term: str) -> None:
    """Statements combine with not, and, or and parentheses."""
    Expression.parse_string(fmt.format(term))


def test_parse_string_camelcase_alias() -> None:
    """Expression.parseString stays available; libhurricane and Tempest call it."""
    assert Expression.parseString == Expression.parse_string
