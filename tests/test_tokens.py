from __future__ import annotations

import datetime
import io
import ipaddress
import pickle
import re
from typing import Any

import ipcalc
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
    """A subnet is stored as an ipcalc network, so runbook bundles pickle as they did in 2.x."""
    subnet = Subnet.parse_string("192.168.0.1/16", parse_all=True)[0]
    assert isinstance(subnet({}), ipcalc.Network)
    assert str(subnet({})) == "192.168.0.0/16"


def test_subnet_with_host_bits() -> None:
    """A subnet written with host bits set still parses, as the network it belongs to."""
    expr = Expression.parse_string("src in 10.0.0.1/8")
    assert expr({"src": "10.2.3.4"})


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


@pytest.mark.parametrize(
    ("expr", "context"),
    [
        ("notable == 1", {"notable": 2}),
        ("nota", {"nota": False}),
        ("not_x", {"not_x": False}),
        ("a == 1 or notable == 1", {"a": 2, "notable": 2}),
    ],
)
def test_symbol_starting_with_keyword(expr: str, context: dict[str, Any]) -> None:
    """A field named like notable is one symbol, not `not` applied to `able`."""
    assert not Expression.parse_string(expr)(context)


@pytest.mark.parametrize(
    "expr", ["A == 1 AND B == 1", "A == 2 OR B == 1", "NOT A == 2", "Not A == 2 aNd B == 1"]
)
def test_boolean_keywords_ignore_case(expr: str) -> None:
    """and, or and not match in any case."""
    assert Expression.parse_string(expr)({"A": 1, "B": 1})


@pytest.mark.parametrize("middle", ["xcx", 5, None, ["c"]])
def test_symbol_through_non_dict_is_missing(middle: Any) -> None:
    """A dotted lookup through a value that isn't a dict finds nothing instead of crashing."""
    sym = Symbol.parse_string("a.b.c", parse_all=True)[0]
    assert sym({"a": {"b": middle}}) is None


@pytest.mark.parametrize(
    ("expr", "context"),
    [
        ("port in 0,80", {"port": 0}),
        ("name in '','x'", {"name": ""}),
        ("name =~ /^$/", {"name": ""}),
    ],
)
def test_falsy_values_still_match(expr: str, context: dict[str, Any]) -> None:
    """0 and '' are real values; `in` and `=~` only skip a field that's missing."""
    assert Expression.parse_string(expr)(context)


@pytest.mark.parametrize(
    ("expr", "context"),
    [("a in b", {"a": "x"}), ("a in b", {"b": ["x"]}), ("a =~ /x/", {})],
)
def test_missing_side_is_false(expr: str, context: dict[str, Any]) -> None:
    """A missing field on either side of `in` or `=~` is False, not an error."""
    assert not Expression.parse_string(expr)(context)


def test_regex_on_number_raises() -> None:
    """=~ needs a string; 0 now reaches the regex and raises like any other number."""
    with pytest.raises(TypeError):
        Expression.parse_string("a =~ /0/")({"a": 0})


@pytest.mark.parametrize(
    ("ips", "expected"),
    [
        (["localhost", "10.1.2.3"], True),
        (["10.1.2.3", "localhost"], True),
        (["192.168.0.1", "10.1.2.3"], True),
        (["192.168.0.1", "localhost"], False),
        ([(), "10.1.2.3"], True),
        ([("10.1.2.3", None), "10.1.2.3"], True),
        ([("10.0.0.0", 8)], False),  # a tuple isn't an IP, even one ipaddress reads as a network
        ([], False),
    ],
)
def test_list_in_subnet_checks_each_item(ips: list[str], expected: bool) -> None:
    """A list matches a subnet when any item is inside it; items that aren't IPs are skipped."""
    expr = Expression.parse_string("src in 10.0.0.0/8")
    assert expr({"src": ips}) is expected


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("10.1.2.3", True),
        (167837955, True),  # 10.1.2.3 as an int
        ("10.1.0.0/16", True),
        ("10.0.0.0/8", True),
        ("10.0.0.0/7", False),  # bigger than the subnet, so not inside it
        ("11.0.0.1", False),
        ("::1", False),
        ("localhost", False),
        ("10.1", False),  # ipcalc's shorthand for 10.1.0.0; not an IP to ipaddress
        (3.5, False),
    ],
)
def test_in_subnet(src: Any, expected: bool) -> None:
    """IPs and subnets, as strings or ints, match inside the subnet; anything else is False."""
    assert Expression.parse_string("src in 10.0.0.0/8")({"src": src}) is expected


@pytest.mark.parametrize("expr", ["a < 5", "a <= 5", "a > 5", "a >= 5", "5 < a", "a > b", "x > a"])
def test_comparison_with_missing_field_is_false(expr: str) -> None:
    """<, <=, > and >= are False when either side is missing, instead of raising."""
    assert Expression.parse_string(expr)({"x": 1}) is False


@pytest.mark.parametrize(
    ("expr", "context"),
    [
        ("a < 5", {"a": "x"}),
        (
            "created > 2024-01-01",
            {"created": datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)},
        ),
    ],
)
def test_comparison_type_mismatch_raises(expr: str, context: dict[str, Any]) -> None:
    """Values that can't be compared still raise, so a wrong filter stays visible."""
    with pytest.raises(TypeError):
        Expression.parse_string(expr)(context)


def test_time_uses_the_day_it_is_evaluated(time_machine: Any) -> None:
    """A time literal means that time today, where today is when the filter runs, not parses."""
    time_machine.move_to(datetime.datetime(2025, 1, 1, 9, 0))
    expr = Expression.parse_string("t > 12:00:00")
    time_machine.move_to(datetime.datetime(2025, 1, 2, 9, 0))
    assert expr({"t": datetime.datetime(2025, 1, 2, 13, 0)})
    assert not expr({"t": datetime.datetime(2025, 1, 1, 13, 0)})


@pytest.mark.parametrize("value", ["2015-01-01T12:34:56", "2015-01-01 12:34:56"])
def test_datetime_literal(value: str) -> None:
    """A date with a time is that exact moment."""
    expr = Expression.parse_string(f"t == {value}")
    assert expr({"t": datetime.datetime(2015, 1, 1, 12, 34, 56)})


@pytest.mark.parametrize(
    ("context", "expected"),
    [({"a": "x"}, True), ({"a": [1]}, True), ({"a": 0}, False), ({"a": ""}, False), ({}, False)],
)
def test_bare_field_returns_bool(context: dict[str, Any], expected: bool) -> None:
    """A filter that is just a field name is True when the field's value is truthy."""
    assert Expression.parse_string("a")(context) is expected


@pytest.mark.parametrize(
    "network", [ipaddress.ip_network("10.0.0.0/8"), ipcalc.Network("10.0.0.0/8")]
)
@pytest.mark.parametrize(
    ("src", "expected"), [("10.1.2.3", True), ("10.0.0.0/7", False), ("localhost", False)]
)
def test_in_subnet_from_either_network_type(network: Any, src: str, expected: bool) -> None:
    """`in` checks the same way whether the subnet is an ipaddress or an ipcalc network.

    A runbook bundle pickled by filtration 2.x holds ipcalc networks, and this version must
    evaluate those exactly as it evaluates its own.
    """
    assert Expression.parse_string("src in net")({"src": src, "net": network}) is expected


# Every name a pickled filter may reference; each exists in filtration 2.3.2, so a pickle
# built with this version can be loaded there. This checks names only, not results.
# Bare time literals are left out on purpose: they pickle as datetime.time, which 2.x
# can't compare, so filters meant for 2.x readers can't use them.
NAMES_OLDER_READERS_HAVE = {
    "_operator.eq",
    "_operator.ge",
    "_operator.gt",
    "_operator.le",
    "_operator.lt",
    "_operator.ne",
    "datetime.datetime",
    "filtration.Token",
    "filtration._And",
    "filtration._List",
    "filtration._Not",
    "filtration._Or",
    "filtration._Regex",
    "filtration._Statement",
    "filtration._Subnet",
    "filtration._Symbol",
    "filtration.in_op",
    "filtration.re_op",
    "ipcalc.Network",
    "pyparsing.results.ParseResults",
    "re._compile",
}


@pytest.mark.parametrize(
    "expr",
    [
        "a == 1 and b != 'x'",
        "a in 'x','y'",
        "src in 10.169.252.0/24",
        "a =~ /x/i or not b",
        "a.b >= 2015-01-01 and c < 2015-01-01T12:00:00",
    ],
)
def test_pickled_filter_uses_only_names_older_readers_have(expr: str) -> None:
    """A pickled filter references only classes and functions filtration 2.3.2 also has."""
    seen: set[str] = set()

    class Recorder(pickle.Unpickler):
        def find_class(self, module: str, name: str) -> Any:
            seen.add(f"{module}.{name}")
            return super().find_class(module, name)

    parsed = Expression.parse_string(expr)
    restored = Recorder(io.BytesIO(pickle.dumps(parsed))).load()
    assert seen <= NAMES_OLDER_READERS_HAVE, seen - NAMES_OLDER_READERS_HAVE
    assert isinstance(restored({}), bool)


@pytest.mark.parametrize(
    ("context", "equal"),
    [
        ({}, False),
        ({"src": "hello"}, False),
        ({"src": ("10.0.0.0", 8)}, False),
        ({"src": "10.0.0.0/8"}, True),
        ({"src": "10.0.0.1/8"}, True),  # host bits normalize, as they do in the literal
        ({"src": "10.0.0.0/16"}, False),
        ({"src": "11.0.0.1"}, False),
    ],
)
def test_equality_against_subnet(context: dict[str, Any], equal: bool) -> None:
    """== and != against a subnet compare networks; a missing or non-IP field just isn't equal."""
    assert Expression.parse_string("src == 10.0.0.0/8")(context) is equal
    assert Expression.parse_string("src != 10.0.0.0/8")(context) is not equal
