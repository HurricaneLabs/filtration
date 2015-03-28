from pyparsing import alphas,nums
from pyparsing import Combine,Forward,Group,CaselessLiteral,Keyword,Literal,MatchFirst,OneOrMore
from pyparsing import Optional,ParseException,QuotedString,Suppress,Word
from pyparsing import opAssoc,operatorPrecedence,quotedString,removeQuotes

from .parser import parseRegex,parseSubnet,parseSymbol,parseValue,parseList
from .parser import parseAnd,parseOr,parseNot
from .parser import parseExpression,parseStatement


RegexFlags = Word("ims")
Regex = (QuotedString("/") + Optional(RegexFlags)).setParseAction(parseRegex)

Ip4Octet = Word(nums, max=3)
Ip4Addr = Combine(Ip4Octet + "." + Ip4Octet + "." + Ip4Octet + "." + Ip4Octet)
Subnet = Combine(Ip4Addr + "/" + Word(nums, max=2)).setParseAction(parseSubnet)

Symbol = Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_")).setParseAction(parseSymbol)
Value = MatchFirst([
    quotedString.setParseAction(removeQuotes),
    Word(nums).setParseAction(lambda s,l,t: int(t[0])),
]).setParseAction(parseValue)

List = Group(Value + OneOrMore(Suppress(Literal(",")) + Value)).setParseAction(parseList)

# Operators
ComparisonOp = MatchFirst([
    Literal("=="),
    Literal("!="),
    Literal("<="),
    Literal("<"),
    Literal(">="),
    Literal(">"),
    Keyword("in"),
    Literal("=~"),
])

BooleanOps = [
    (CaselessLiteral("not"), 1, opAssoc.RIGHT, parseNot),
    (CaselessLiteral("and"), 2, opAssoc.LEFT, parseAnd),
    (CaselessLiteral("or"), 2, opAssoc.LEFT, parseOr),
]

LHS = Symbol | Value
RHS = Symbol | Subnet | List | Value | Regex

Statement = (LHS + Optional(ComparisonOp + RHS)).setParseAction(parseStatement)
Expression = operatorPrecedence(Statement, BooleanOps).setParseAction(parseExpression)
