import itertools

from pyparsing import alphas,nums
from pyparsing import Combine,Forward,Group,CaselessLiteral,Keyword,Literal,MatchFirst,OneOrMore
from pyparsing import Optional,ParseException,QuotedString,Suppress,Word
from pyparsing import opAssoc,operatorPrecedence,quotedString,removeQuotes


def compileExpression(string, loc, tokens):
    pass


def compileFilter(string, loc, tokens):
    pass


class FiltrationBase:
    token = None

    @classmethod
    def parseString(cls, *args, **kwargs):
        return cls.token.parseString(*args, **kwargs)[0]

class BaseToken(FiltrationBase):
    compile_error = "Error parsing: {0}"

    def __init__(self, string, loc, tokens):
        try:
            self.compile(tokens)
        except:
            raise ParseException(string, loc, self.compile_error.format(string))

    def compile(self, tokens):
        raise NotImplementedError

    def __call__(self, context):
        return None

_Value = Forward()
class Value(BaseToken):
    token = _Value

    def compile(self, tokens):
        self.value = tokens[0]

    def __call__(self, context):
        return self.value


_Regex = Forward()
class Regex(BaseToken):
    compile_error = "Invalid regex: {0}"
    token = _Regex

    def compile(self, tokens):
        import re
        self.rex = re.compile(tokens[0])

    def __call__(self, context):
        return self.rex

_Subnet = Forward()
class Subnet(BaseToken):
    compile_error = "Invalid subnet: {0}"
    token = _Subnet

    def compile(self, tokens):
        import ipcalc
        self.subnet = ipcalc.Network(tokens[0])

    def __call__(self, context):
        return self.subnet

_Symbol = Forward()
class Symbol(BaseToken):
    token = _Symbol

    def compile(self, tokens):
        self.value = tokens[0]

    def __call__(self, context):
        parts = self.value.split(".")
        value = context
        for part in parts:
            if part in value:
                value = value[part]
            else:
                value = None
                break
        return value

_Expression = Forward()
class Expression(FiltrationBase):
    token = _Expression

    def __init__(self, string, loc, tokens):
        if len(tokens) == 1:
            tokens = (tokens[0], None, None)
        (self.lhs, self.op, self.rhs) = tokens

_Filter = Forward()
class Filter(FiltrationBase):
    token = _Filter

_Regex << QuotedString("/").setParseAction(Regex)

_Ip4Octet = Word(nums, max=3)
_Ip4Addr = Combine(_Ip4Octet + "." + _Ip4Octet + "." + _Ip4Octet + "." + _Ip4Octet)
_Subnet << Combine(_Ip4Addr + "/" + Word(nums, max=2)).setParseAction(Subnet)

_Symbol << Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_")).setParseAction(Symbol)
_Value << MatchFirst([
    quotedString.setParseAction(removeQuotes),
    Word(nums).setParseAction(lambda s,l,t: int(t[0])),
]).setParseAction(Value)

List = Group(_Value + OneOrMore(Suppress(Literal(",")) + _Value))

# Operators
ComparisonOp = MatchFirst([
    Literal("=="),
    Literal("!="),
    Literal("<"),
    Literal("<="),
    Literal(">"),
    Literal(">="),
    Keyword("in"),
    Literal("=~"),
])

BooleanOps = [
    (CaselessLiteral("not"), 1, opAssoc.RIGHT, compileFilter),
    (CaselessLiteral("and"), 2, opAssoc.LEFT, compileFilter),
    (CaselessLiteral("or"), 2, opAssoc.LEFT, compileFilter),
]

LHS = _Symbol | _Value
RHS = _Symbol | _Subnet | List | _Value | _Regex

_Expression << (LHS + Optional(ComparisonOp + RHS)).setParseAction(Expression)
_Filter << operatorPrecedence(_Expression, BooleanOps)
