from pyparsing import *


def compileRegex(string, length, tokens):
    import re
    try:
        return re.compile(tokens[0])
    except:
        raise ParseException(string, length, "Invalid regular expression")


def compileIpAddress(string, length, tokens):
    import ipcalc
    try:
        return ipcalc.Network(tokens[0])
    except:
        raise ParseException(string, length, "Invalid subnet: {0}".format(tokens[0]))


def compileExpression(string, length, tokens):
    pass


def compileFilter(string, length, tokens):
    pass


Regex = QuotedString("/").setParseAction(compileRegex)

Ip4Octet = Word(nums, max=3)
Ip4Addr = Combine(Ip4Octet + "." + Ip4Octet + "." + Ip4Octet + "." + Ip4Octet)
Subnet = Combine(Ip4Addr + "/" + Word(nums, max=2)).setParseAction(compileIpAddress)

Symbol = Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_"))
Value = MatchFirst([
    quotedString.setParseAction(removeQuotes),
    Word(nums).setParseAction(lambda s,l,t: int(t[0])),
])

List = Group(Value + OneOrMore(Suppress(Literal(",")) + Value))

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

LHS = Symbol | Value
RHS = Symbol | Subnet | List | Value | Regex

Expression = (LHS + Optional(ComparisonOp + RHS)).setParseAction(compileExpression)
Filter = operatorPrecedence(Expression, BooleanOps)
