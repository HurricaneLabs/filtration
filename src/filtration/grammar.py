from pyparsing import alphas,nums
from pyparsing import Combine,Forward,Group,CaselessLiteral,Keyword,Literal,MatchFirst,OneOrMore
from pyparsing import Optional,ParseException,QuotedString,Suppress,Word
from pyparsing import opAssoc,operatorPrecedence,quotedString,removeQuotes

from .parser import parseRegex,parseSubnet,parseSymbol,parseValue,parseList
from .parser import parseAnd,parseOr,parseNot
from .parser import parseExpression,parseStatement
from .parser import parseDate,parseTime,parseDateTime


Year = Word(nums, max=4).setParseAction(lambda s,l,t: int(t[0]))
Month = Word(nums, max=2).setParseAction(lambda s,l,t: int(t[0]))
DayOfMonth = Word(nums, max=2).setParseAction(lambda s,l,t: int(t[0]))

Hour = Word(nums, max=2).setParseAction(lambda s,l,t: int(t[0]))
Minute = Word(nums, max=2).setParseAction(lambda s,l,t: int(t[0]))
Second = Word(nums, max=2).setParseAction(lambda s,l,t: int(t[0]))

Date = (Year + Suppress("-") + Month + Suppress("-") + DayOfMonth).setParseAction(parseDate)
Time = (Hour + Suppress(":") + Minute + Suppress(":") + Second).setParseAction(parseTime)
DateTime = (Date + Suppress(Optional("T")) + Time).setParseAction(parseDateTime)

RegexFlags = Word("ims")
Regex = (QuotedString("/") + Optional(RegexFlags)).setParseAction(parseRegex)

Ip4Octet = Word(nums, max=3)
Ip4Addr = Combine(Ip4Octet + "." + Ip4Octet + "." + Ip4Octet + "." + Ip4Octet)
Subnet = Combine(Ip4Addr + "/" + Word(nums, max=2)).setParseAction(parseSubnet)

Symbol = Word((alphas + "_"), bodyChars=(alphas + nums + "." + "_")).setParseAction(parseSymbol)
Value = MatchFirst([
    DateTime,
    Date,
    Time,
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
