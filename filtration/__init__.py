import datetime
import operator
import re
from functools import reduce

import ipcalc
from pyparsing import alphas, nums
from pyparsing import CaselessLiteral, Combine, Group, Keyword, Literal, MatchFirst, OneOrMore
from pyparsing import infix_notation, OpAssoc, Optional, ParseException, quoted_string
from pyparsing import QuotedString, remove_quotes, Suppress, Word, ZeroOrMore


class Token:
    def __init__(self, toks):
        compiler = getattr(self, "compiler", None)
        if callable(compiler):
            self.value = compiler(*toks)  # pylint: disable=not-callable
        else:
            try:
                self.value = toks[0]
            except TypeError:  # pragma: no cover
                self.value = toks

    def __call__(self, ctx):
        # pylint: disable=unused-argument
        return self.value


Year = Word(nums, max=4).set_parse_action(lambda toks: int(toks[0]))
Month = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Day = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))

Hour = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Minute = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))
Second = Word(nums, max=2).set_parse_action(lambda toks: int(toks[0]))

Date = (Year + Suppress("-") + Month + Suppress("-") + Day).set_parse_action(
    lambda toks: datetime.datetime.combine(datetime.date(*toks), datetime.time.min)
)
Time = (Hour + Suppress(":") + Minute + Suppress(":") + Second).set_parse_action(
    lambda toks: datetime.datetime.combine(datetime.date.today(), datetime.time(*toks))
)
DateTime = (Date + Suppress(Optional("T")) + Time).set_parse_action(
    lambda toks: datetime.datetime.combine(toks[0].date(), toks[1].time())
)


class _Regex(Token):
    def compiler(self, pattern, flags):
        # pylint: disable=no-self-use
        try:
            return re.compile(pattern, flags)
        except re.error as exc:
            raise ParseException(str(exc)) from exc


RegexFlag = Word("ims", exact=1).set_parse_action(
    lambda toks: getattr(re, toks[0].upper())
)
RegexFlags = ZeroOrMore(RegexFlag).set_parse_action(
    lambda toks: reduce(lambda a, b: a | b, toks, 0)
)
Regex = (QuotedString("/") + RegexFlags).set_parse_action(_Regex)

Octet = Word(nums, max=3).addCondition(lambda toks: int(toks[0]) <= 255)
IpAddr = Combine(Octet + "." + Octet + "." + Octet + "." + Octet)
Cidr = Word(nums, max=2).addCondition(lambda toks: int(toks[0]) <= 32)


class _Subnet(Token):
    def compiler(self, subnet):
        # pylint: disable=no-self-use
        return ipcalc.Network(subnet)


Subnet = Combine(IpAddr + "/" + Cidr).set_parse_action(_Subnet)


class _Symbol(Token):
    def __call__(self, ctx):
        parts = self.value.split(".")
        value = ctx
        for part in parts:
            if part in value:
                value = value[part]
            else:
                value = None
                break
        return value


Symbol = Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_")).set_parse_action(_Symbol)


Value = MatchFirst([
    DateTime,
    Date,
    Time,
    quoted_string.set_parse_action(remove_quotes),
    Word(nums).set_parse_action(lambda toks: int(toks[0])),
]).set_parse_action(Token)


class _List(Token):
    def __call__(self, ctx):
        return [item(ctx) for item in self.value]


List = Group(Value + OneOrMore(Suppress(Literal(",")) + Value)).set_parse_action(_List)


def in_op(lhs, rhs):
    if not (lhs and rhs):
        return False

    try:
        return operator.contains(rhs, lhs)
    except ValueError:
        return False


def re_op(lhs, rhs):
    if not (lhs and rhs):
        return False

    if isinstance(lhs, list):
        return any(rhs.search(item) for item in lhs)

    return bool(rhs.search(lhs))


# Operators
ComparisonOp = MatchFirst([
    Literal("==").set_parse_action(lambda toks: operator.eq),
    Literal("!=").set_parse_action(lambda toks: operator.ne),
    Literal("<=").set_parse_action(lambda toks: operator.le),
    Literal("<").set_parse_action(lambda toks: operator.lt),
    Literal(">=").set_parse_action(lambda toks: operator.ge),
    Literal(">").set_parse_action(lambda toks: operator.gt),
    Keyword("in").set_parse_action(lambda toks: in_op),
    Literal("=~").set_parse_action(lambda toks: re_op),
])


class _Not(Token):
    def compiler(self, *toks):
        # pylint: disable=no-self-use
        return toks[0][1]

    def __call__(self, ctx):
        return not self.value(ctx)


class _And(Token):
    def compiler(self, *toks):
        # pylint: disable=no-self-use
        return toks[0][0::2]

    def __call__(self, ctx):
        return all(item(ctx) for item in self.value)


class _Or(Token):
    def compiler(self, *toks):
        # pylint: disable=no-self-use
        return toks[0][0::2]

    def __call__(self, ctx):
        return any(item(ctx) for item in self.value)


BooleanOps = [
    (CaselessLiteral("not"), 1, OpAssoc.RIGHT, _Not),
    (CaselessLiteral("and"), 2, OpAssoc.LEFT, _And),
    (CaselessLiteral("or"), 2, OpAssoc.LEFT, _Or),
]

LHS = Symbol | Value | Regex
RHS = Symbol | Subnet | List | Value | Regex


class _Statement:
    def __init__(self, lhs, op=None, rhs=None):
        self.lhs = lhs
        self.op = op  # pylint: disable=invalid-name
        self.rhs = rhs

    def __call__(self, ctx):
        if self.op is None:
            return self.lhs(ctx)

        return self.op(self.lhs(ctx), self.rhs(ctx))


Statement = (LHS + Optional(ComparisonOp + RHS)).set_parse_action(
    lambda toks: _Statement(*toks)
)


class Expression:
    @classmethod
    def parse_string(cls, *args, **kwargs):
        expr = infix_notation(Statement, BooleanOps).set_parse_action(
            lambda toks: _Statement(*toks)
        )

        return expr.parse_string(*args, **kwargs)[0]

    parseString = parse_string
