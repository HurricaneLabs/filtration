from pyparsing import ParseException


qs_operations = {
    "eq": "==",
    "ne": "!=",
    "lt": "<",
    "le": "<=",
    "gt": ">",
    "ge": ">=",
}


def parseRegex(*args, **kwargs):
    from .tokens import Regex
    return Regex(*args, **kwargs)

def parseSubnet(*args, **kwargs):
    from .tokens import Subnet
    return Subnet(*args, **kwargs)

def parseValue(*args, **kwargs):
    from .tokens import Value
    return Value(*args, **kwargs)

def parseSymbol(*args, **kwargs):
    from .tokens import Symbol
    return Symbol(*args, **kwargs)

def parseList(*args, **kwargs):
    from .tokens import List
    return List(*args, **kwargs)

def parseStatement(*args, **kwargs):
    from .tokens import Statement
    return Statement(*args, **kwargs)

def parseExpression(*args, **kwargs):
    from .tokens import Expression
    return Expression(*args, **kwargs)

def parseNot(*args, **kwargs):
    from .tokens import NotStatement
    return NotStatement(*args, **kwargs)

def parseAnd(*args, **kwargs):
    from .tokens import AndStatement
    return AndStatement(*args, **kwargs)

def parseOr(*args, **kwargs):
    from .tokens import OrStatement
    return OrStatement(*args, **kwargs)

def parseQsChunk(chunk):
    import urllib.parse

    (qs_lhs, qs_rhs) = chunk.split("=", 1)

    qs_lhs = urllib.parse.unquote(qs_lhs)
    qs_rhs = urllib.parse.unquote(qs_rhs)

    qs_lhs_parts = qs_lhs.split("__")
    qs_op = qs_lhs_parts.pop(-1)
    lhs = ".".join(qs_lhs_parts)

    if qs_op in qs_operations:
        from .grammar import Value
        op = qs_operations[qs_op]
        if op in ("<", "<=", ">", ">="):
            rhs = int(qs_rhs)
        else:
            rhs = "'{0}'".format(qs_rhs)
    elif qs_op in ("contains", "icontains"):
        op = "=~"
        rhs = "/{0}/".format(qs_rhs)
    elif qs_op in ("startswith", "istartswith"):
        op = "=~"
        rhs = "/^{0}/".format(qs_rhs)
    elif qs_op in ("endswith", "iendswith"):
        op = "=~"
        rhs = "/{0}$/".format(qs_rhs)

    if qs_op in ("icontains", "istartswith", "iendswith"):
        rhs += "i"

    return "{0} {1} {2}".format(lhs, op, rhs)

def parseDate(string, loc, tokens):
    import datetime
    d = datetime.date(*tokens)
    return datetime.datetime.combine(d, datetime.time.min)

def parseTime(string, loc, tokens):
    import datetime
    t = datetime.time(*tokens)
    return datetime.datetime.combine(datetime.date.today(), t)

def parseDateTime(string, loc, tokens):
    import datetime
    (date, time) = tokens[:2]
    return datetime.datetime.combine(date.date(), time.time())
