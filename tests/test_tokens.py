from __future__ import annotations

import datetime
import re
from typing import Any

import pytest

from filtration import Expression, Regex, Subnet, Symbol, Value

REGEX_EVALUATE = [
    ("/abc/", re.compile("abc")),
    ("/abc/i", re.compile("abc", flags=re.IGNORECASE)),
    ("/abc/m", re.compile("abc", flags=re.MULTILINE)),
    ("/abc/s", re.compile("abc", flags=re.DOTALL)),
    ("/abc/ims", re.compile("abc", flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)),
]

# (expression that should be true, expression that should be false)
EXPRESSION_EVALUATE = [
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


@pytest.fixture
def context() -> dict[str, Any]:
    """An evaluation context with one value of each type the grammar compares."""
    ctx: dict[str, Any] = {
        "symbol_true": True,
        "symbol_false": False,
        "symbol_int": 1,
        "symbol_str": "a",
        "symbol_dt": datetime.datetime.now(),
        "symbol_list": ["abcde", "cdefg"],
    }
    ctx["dict"] = ctx
    return ctx


def test_evaluate_symbol() -> None:
    """A symbol evaluates to its value in the context."""
    sym = Symbol.parse_string("symbol", parse_all=True)[0]
    assert sym({"symbol": "value"}) == "value"


def test_evaluate_value() -> None:
    """A quoted value evaluates to the string without quotes."""
    val = Value.parse_string("'value'", parse_all=True)[0]
    assert val({}) == "value"


@pytest.mark.parametrize(("expr", "expected"), REGEX_EVALUATE)
def test_evaluate_regex(expr: str, expected: re.Pattern) -> None:
    """A regex evaluates to a compiled pattern with the flags given."""
    rex = Regex.parse_string(expr, parse_all=True)[0]
    result = rex({})
    assert result.pattern == expected.pattern
    assert result.flags == expected.flags


def test_evaluate_subnet() -> None:
    """A subnet evaluates to a network object."""
    subnet = Subnet.parse_string("192.168.0.0/16", parse_all=True)[0]
    assert subnet({}).network() == "192.168.0.0"
    assert subnet({}).size() == 2**16


@pytest.mark.parametrize(("expr_true", "expr_false"), EXPRESSION_EVALUATE)
def test_evaluate_expression(
    context: dict[str, Any], expr_true: str | None, expr_false: str
) -> None:
    """Each operator gives the expected result against the context."""
    if expr_true:
        assert Expression.parse_string(expr_true, parse_all=True)(context)
    assert not Expression.parse_string(expr_false, parse_all=True)(context)


def test_subnet_contains() -> None:
    """`in` a subnet matches IPs inside it and rejects non-IPs."""
    expr = Expression.parse_string("src in 127.0.0.0/8", parse_all=True)
    assert expr({"src": "127.0.0.1"})
    assert not expr({"src": "localhost"})
