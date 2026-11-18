import datetime
import ipaddress
import operator
import re
from functools import reduce

from pyparsing import (
    CaselessKeyword,
    Combine,
    Group,
    Keyword,
    Literal,
    MatchFirst,
    OneOrMore,
    OpAssoc,
    Optional,
    ParseException,
    ParseFatalException,
    QuotedString,
    Suppress,
    Word,
    ZeroOrMore,
    alphas,
    infix_notation,
    nums,
    quoted_string,
    remove_quotes,
)


class Token:
    def __init__(self, toks):
        compiler = getattr(self, "compiler", None)
        if callable(compiler):
            self.value = compiler(*toks)
        else:
            try:
                self.value = toks[0]
            except TypeError:  # pragma: no cover
                self.value = toks

    def __call__(self, ctx):
        if isinstance(self.value, datetime.time):
            # a bare time means that time on the day the filter runs
            return datetime.datetime.combine(datetime.date.today(), self.value)
        return self.value


Year = Word(nums, max=4).set_parse_action(lambda toks: int(toks[0]))
Month = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Day = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))

Hour = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Minute = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Second = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))


def _datetime_action(build):
    # datetime raises ValueError for things like month 13; make that a parse error.
    # Fatal, so the Value alternatives can't fall back to reading 2015-13-01 as 2015
    def action(s, loc, toks):
        try:
            return build(toks)
        except ValueError as exc:
            raise ParseFatalException(s, loc, str(exc)) from exc

    return action


Date = (Year + Suppress("-") + Month + Suppress("-") + Day).set_parse_action(
    _datetime_action(
        lambda toks: datetime.datetime.combine(datetime.date(*toks), datetime.time.min)
    )
)
# a plain time, not a datetime: the day is filled in when the filter runs (Token.__call__)
Time = (Hour + Suppress(":") + Minute + Suppress(":") + Second).set_parse_action(
    _datetime_action(lambda toks: datetime.time(*toks))
)
DateTime = (Date + Suppress(Optional("T")) + Time).set_parse_action(
    lambda toks: datetime.datetime.combine(toks[0].date(), toks[1])
)


class _Regex(Token):
    def compiler(self, pattern, flags):
        try:
            return re.compile(pattern, flags)
        except re.error as exc:
            raise ParseException(str(exc)) from exc


RegexFlag = Word("ims", exact=1).set_parse_action(lambda toks: getattr(re, toks[0].upper()))
# flags must touch the closing slash, so `/x/ in b` reads in as the operator
RegexFlags = (
    ZeroOrMore(RegexFlag)
    .leave_whitespace()
    .set_parse_action(lambda toks: reduce(lambda a, b: a | b, toks, 0))
)
Regex = (QuotedString("/") + RegexFlags).set_parse_action(_Regex)

Octet = Word(nums, max=3).add_condition(lambda toks: int(toks[0]) <= 255)
IpAddr = Combine(Octet + "." + Octet + "." + Octet + "." + Octet)
Cidr = Word(nums, max=2).add_condition(lambda toks: int(toks[0]) <= 32)


class _Subnet(Token):
    def compiler(self, subnet):
        # strict=False so 10.0.0.1/8 means 10.0.0.0/8 rather than an error
        return ipaddress.ip_network(subnet, strict=False)


Subnet = Combine(IpAddr + "/" + Cidr).set_parse_action(_Subnet)


class _Symbol(Token):
    def __call__(self, ctx):
        # If symbol is a literal 'a.b' and exists in ctx, return it
        # Imperfect bugfix to allow for fields with literal dots in the root of ctx
        if self.value in ctx:
            return ctx[self.value]

        parts = self.value.split(".")
        value = ctx
        try:
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return None
        except TypeError:
            # a value partway down isn't a dict (a string, number, list or None)
            return None
        return value


Symbol = Word((alphas + "_"), body_chars=(alphas + nums + "." + "_")).set_parse_action(_Symbol)


Value = MatchFirst(
    [
        DateTime,
        Date,
        Time,
        quoted_string.copy().set_parse_action(remove_quotes),
        Word(nums).set_parse_action(lambda toks: int(toks[0])),
    ]
).set_parse_action(Token)


class _List(Token):
    def __call__(self, ctx):
        return [item(ctx) for item in self.value]


List = Group(Value + OneOrMore(Suppress(Literal(",")) + Value)).set_parse_action(_List)


def _in_subnet(item, subnet):
    try:
        # an IP becomes a single-address network, so IPs and subnets share one check
        return ipaddress.ip_network(item, strict=False).subnet_of(subnet)
    except (TypeError, ValueError):
        # not an IP, or IPv6 against an IPv4 subnet
        return False


def in_op(lhs, rhs):
    # only a missing field skips the check; 0 and '' are real values
    if lhs is None or rhs is None:
        return False

    if isinstance(rhs, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        # a list matches a subnet when any item is inside it; one bad item can't sink the rest
        items = lhs if isinstance(lhs, list) else [lhs]
        return any(_in_subnet(item, rhs) for item in items)

    return operator.contains(rhs, lhs)


def re_op(lhs, rhs):
    if lhs is None or rhs is None:
        return False

    if isinstance(lhs, list):
        return any(rhs.search(item) for item in lhs)

    return bool(rhs.search(lhs))


# Operators
ComparisonOp = MatchFirst(
    [
        Literal("==").set_parse_action(lambda toks: operator.eq),
        Literal("!=").set_parse_action(lambda toks: operator.ne),
        Literal("<=").set_parse_action(lambda toks: operator.le),
        Literal("<").set_parse_action(lambda toks: operator.lt),
        Literal(">=").set_parse_action(lambda toks: operator.ge),
        Literal(">").set_parse_action(lambda toks: operator.gt),
        Keyword("in").set_parse_action(lambda toks: in_op),
        Literal("=~").set_parse_action(lambda toks: re_op),
    ]
)


class _Not(Token):
    def compiler(self, *toks):
        return toks[0][1]

    def __call__(self, ctx):
        return not self.value(ctx)


class _And(Token):
    def compiler(self, *toks):
        return toks[0][0::2]

    def __call__(self, ctx):
        return all(item(ctx) for item in self.value)


class _Or(Token):
    def compiler(self, *toks):
        return toks[0][0::2]

    def __call__(self, ctx):
        return any(item(ctx) for item in self.value)


BooleanOps = [
    (CaselessKeyword("not"), 1, OpAssoc.RIGHT, _Not),
    (CaselessKeyword("and"), 2, OpAssoc.LEFT, _And),
    (CaselessKeyword("or"), 2, OpAssoc.LEFT, _Or),
]

LHS = Symbol | Value | Regex
RHS = Symbol | Subnet | List | Value | Regex

ORDERING_OPS = (operator.lt, operator.le, operator.gt, operator.ge)


class _Statement:
    def __init__(self, lhs, op=None, rhs=None):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __call__(self, ctx):
        if self.op is None:
            return self.lhs(ctx)

        lhs, rhs = self.lhs(ctx), self.rhs(ctx)
        # a missing field can't be ordered; checked here, not in a wrapper function,
        # so op stays a stdlib operator that older filtration can still unpickle
        if self.op in ORDERING_OPS and (lhs is None or rhs is None):
            return False

        return self.op(lhs, rhs)


Statement = (LHS + Optional(ComparisonOp + RHS)).set_parse_action(lambda toks: _Statement(*toks))


class Expression:
    @classmethod
    def parse_string(cls, instring, parse_all=True, **kwargs):
        # whole-input match by default, so a typo can't silently drop the rest of a filter;
        # parseAll is the old spelling and has to be mapped here or it can't turn this off
        if "parseAll" in kwargs:
            parse_all = kwargs.pop("parseAll")

        expr = infix_notation(Statement, BooleanOps).set_parse_action(
            lambda toks: _Statement(*toks)
        )

        try:
            return expr.parse_string(instring, parse_all=parse_all, **kwargs)[0]
        except ParseFatalException as exc:
            # callers catch ParseException, which the fatal one isn't a subclass of
            raise ParseException(exc.pstr, exc.loc, exc.msg) from exc

    parseString = parse_string
