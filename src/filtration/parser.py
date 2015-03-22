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
