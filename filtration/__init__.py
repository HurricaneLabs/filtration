# pylint: disable=invalid-name

import datetime
import operator
import re
from functools import reduce

import ipcalc
from pyparsing import alphas, nums
from pyparsing import CaselessLiteral, Combine, Group, Keyword, Literal, MatchFirst, OneOrMore
from pyparsing import opAssoc, operatorPrecedence, Optional, ParseException, quotedString
from pyparsing import QuotedString, removeQuotes, Suppress, Word, ZeroOrMore


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


Year = Word(nums, max=4).setParseAction(lambda toks: int(toks[0]))
Month = Word(nums, max=2).setParseAction(lambda toks: int(toks[0]))
Day = Word(nums, max=2).setParseAction(lambda toks: int(toks[0]))

Hour = Word(nums, max=2).setParseAction(lambda toks: int(toks[0]))
Minute = Word(nums, max=2).setParseAction(lambda toks: int(toks[0]))
Second = Word(nums, max=2).setParseAction(lambda toks: int(toks[0]))

Date = (Year + Suppress("-") + Month + Suppress("-") + Day).setParseAction(
    lambda toks: datetime.datetime.combine(datetime.date(*toks), datetime.time.min)
)
Time = (Hour + Suppress(":") + Minute + Suppress(":") + Second).setParseAction(
    lambda toks: datetime.datetime.combine(datetime.date.today(), datetime.time(*toks))
)
DateTime = (Date + Suppress(Optional("T")) + Time).setParseAction(
    lambda toks: datetime.datetime.combine(toks[0].date(), toks[1].time())
)


class _Regex(Token):
    def compiler(self, pattern, flags):
        # pylint: disable=no-self-use
        try:
            return re.compile(pattern, flags)
        except re.error as e:
            raise ParseException(str(e))


RegexFlag = Word("ims", exact=1).setParseAction(
    lambda toks: getattr(re, toks[0].upper())
)
RegexFlags = ZeroOrMore(RegexFlag).setParseAction(
    lambda toks: reduce(lambda a, b: a | b, toks, 0)
)
Regex = (QuotedString("/") + RegexFlags).setParseAction(_Regex)

Octet = Word(nums, max=3).addCondition(lambda toks: int(toks[0]) <= 255)
IpAddr = Combine(Octet + "." + Octet + "." + Octet + "." + Octet)
Cidr = Word(nums, max=2).addCondition(lambda toks: int(toks[0]) <= 32)


class _Subnet(Token):
    def compiler(self, subnet):
        # pylint: disable=no-self-use
        return ipcalc.Network(subnet)


Subnet = Combine(IpAddr + "/" + Cidr).setParseAction(_Subnet)


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


Symbol = Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_")).setParseAction(_Symbol)


Value = MatchFirst([
    DateTime,
    Date,
    Time,
    quotedString.setParseAction(removeQuotes),
    Word(nums).setParseAction(lambda toks: int(toks[0])),
]).setParseAction(Token)


class _List(Token):
    def __call__(self, ctx):
        return [item(ctx) for item in self.value]


List = Group(Value + OneOrMore(Suppress(Literal(",")) + Value)).setParseAction(_List)

in_op = lambda lhs, rhs: operator.contains(rhs, lhs) if lhs and rhs else False
re_op = lambda lhs, rhs: bool(rhs.search(lhs)) if lhs and rhs else False

# Operators
ComparisonOp = MatchFirst([
    Literal("==").setParseAction(lambda toks: operator.eq),
    Literal("!=").setParseAction(lambda toks: operator.ne),
    Literal("<=").setParseAction(lambda toks: operator.le),
    Literal("<").setParseAction(lambda toks: operator.lt),
    Literal(">=").setParseAction(lambda toks: operator.ge),
    Literal(">").setParseAction(lambda toks: operator.gt),
    Keyword("in").setParseAction(lambda toks: in_op),
    Literal("=~").setParseAction(lambda toks: re_op),
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
        return all([item(ctx) for item in self.value])


class _Or(Token):
    def compiler(self, *toks):
        # pylint: disable=no-self-use
        return toks[0][0::2]

    def __call__(self, ctx):
        return any([item(ctx) for item in self.value])


BooleanOps = [
    (CaselessLiteral("not"), 1, opAssoc.RIGHT, _Not),
    (CaselessLiteral("and"), 2, opAssoc.LEFT, _And),
    (CaselessLiteral("or"), 2, opAssoc.LEFT, _Or),
]

LHS = Symbol | Value
RHS = Symbol | Subnet | List | Value | Regex


class _Statement:
    def __init__(self, lhs, op=None, rhs=None):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __call__(self, ctx):
        if self.op is None:
            return self.lhs(ctx)

        return self.op(self.lhs(ctx), self.rhs(ctx))


Statement = (LHS + Optional(ComparisonOp + RHS)).setParseAction(
    lambda toks: _Statement(*toks)
)


class Expression:
    @classmethod
    def parseString(cls, *args, **kwargs):
        expr = operatorPrecedence(Statement, BooleanOps).setParseAction(
            lambda toks: _Statement(*toks)
        )

        return expr.parseString(*args, **kwargs)[0]
