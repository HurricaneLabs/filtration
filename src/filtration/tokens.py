import itertools
import operator

from pyparsing import ParseException

from . import grammar


class FiltrationBase:
    token = None

    @classmethod
    def parseString(cls, *args, **kwargs):
        return cls.token.parseString(*args, **kwargs)[0]

    @classmethod
    def build(cls, *tokens):
        return cls("", 0, tokens)

class BaseToken(FiltrationBase):
    compile_error = "Error parsing: {0}"

    def __init__(self, string, loc, tokens):
        compiler = getattr(self, "compile", None)
        try:
            compiler(tokens)
        except:
            raise ParseException(string, loc, self.compile_error.format(string))

class Value(BaseToken):
    token = grammar.Value

    @property
    def as_mongo(self):
        return self.value

    def compile(self, tokens):
        self.value = tokens[0]

    def __call__(self, context):
        return self.value

    def __repr__(self):
        return repr(self.value)


class Regex(BaseToken):
    compile_error = "Invalid regex: {0}"
    token = grammar.Regex

    @property
    def flags(self):
        import re
        flags = 0
        for flag in self._flags:
            flags |= getattr(re, flag.upper())
        return flags

    @property
    def as_mongo(self):
        return repr(self)

    def compile(self, tokens):
        import re
        self._raw = tokens[0]

        if len(tokens) > 1:
            self._flags = tokens[1]
        else:
            self._flags = ""

        self.rex = re.compile(tokens[0], flags=self.flags)

    def __call__(self, context):
        return self.rex

    def __repr__(self):
        return "/{0}/{1}".format(self._raw, self._flags)

class Subnet(BaseToken):
    compile_error = "Invalid subnet: {0}"
    token = grammar.Subnet

    @property
    def as_mongo(self):
        return list(self.subnet)

    def compile(self, tokens):
        import ipcalc
        self.subnet = ipcalc.Network(tokens[0])

    def __call__(self, context):
        return self.subnet

    def __repr__(self):
        return str(self.subnet)

class List(BaseToken):
    token = grammar.List

    @property
    def as_mongo(self):
        return [ item.as_mongo for item in self.items ]

    def compile(self, tokens):
        self.items = tokens[0].asList()

    def __call__(self, context):
        ret = [ item(context) for item in self.items ]
        return ret

    def __repr__(self):
        return repr(self.items)

class Symbol(BaseToken):
    token = grammar.Symbol

    @property
    def as_mongo(self):
        return self.value

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

    def __repr__(self):
        return self.value

class Statement(FiltrationBase):
    token = grammar.Statement

    def __init__(self, string, loc, tokens):
        if len(tokens) == 1:
            tokens = (tokens[0], None, None)
        (self.lhs, self.op, self.rhs) = tokens

    @property
    def as_mongo(self):
        if self.op is None:
            return { self.lhs.as_mongo: {"$exists": True} }

        as_mongo = {
            "==": lambda lhs,rhs: { lhs: rhs },
            "!=": lambda lhs,rhs: { lhs: {"$ne": rhs } },
            "<": lambda lhs,rhs: { lhs: {"$lt": rhs } },
            "<=": lambda lhs,rhs: { lhs: {"$lte": rhs } },
            ">": lambda lhs,rhs: { lhs: {"$gt": rhs } },
            ">=": lambda lhs,rhs: { lhs: {"$gte": rhs } },
            "=~": lambda lhs,rhs: { lhs: {"$regex": rhs } },
            "in": lambda lhs,rhs: { lhs: {"$in": rhs } },
        }[self.op]

        return as_mongo(self.lhs.as_mongo, self.rhs.as_mongo)

    def __call__(self, context):
        lhs = self.lhs(context)

        if self.op is None:
            return bool(lhs)

        func = {
            "==": operator.eq,
            "!=": operator.ne,
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "in": lambda lhs,rhs: operator.contains(rhs,lhs),
            "=~": lambda lhs,rhs: bool(rhs.search(lhs)),
        }[self.op]

        rhs = self.rhs(context)

        return func(lhs, rhs)

    def __repr__(self):
        if self.op is None:
            return repr(self.lhs)
        return "{0} {1} {2}".format(repr(self.lhs), self.op, repr(self.rhs))

class Expression(FiltrationBase):
    token = grammar.Expression

    @property
    def as_mongo(self):
        return self.lhs.as_mongo

    @classmethod
    def parseQsString(cls, qs):
        from .parser import parseQsChunk
        return cls.parseString(" and ".join([parseQsChunk(_) for _ in qs.split("&")]))

    @classmethod
    def buildSimpleExpression(cls, lhs, op, rhs):
        lhs = Symbol.build(lhs)
        rhs = Value.build(rhs)
        return cls.build(Statement.build(lhs, op, rhs))

    def __init__(self, string, loc, tokens):
        self.lhs = tokens[0]

    def __call__(self, context):
        return self.lhs(context)

    def __repr__(self):
        return repr(self.lhs)

class BaseStatement:
    @classmethod
    def build(cls, *tokens):
        return cls("", 0, tokens)

class NotStatement(BaseStatement):
    @property
    def as_mongo(self):
        return {"$not": self.lhs.as_mongo}

    def __init__(self, string, loc, tokens):
        _,self.lhs = tokens[0]

    def __call__(self, context):
        lhs = self.lhs(context)
        return not lhs

    def __repr__(self):
        return "not {0}".format(repr(self.lhs))

class AndStatement(BaseStatement):
    @property
    def as_mongo(self):
        return {"$and": [ item.as_mongo for item in self.items ]}

    def __init__(self, string, loc, tokens):
        self.items = tokens[0][0::2]

    def __call__(self, context):
        return all([ item(context) for item in self.items ])

    def __repr__(self):
        return "({0})".format(" and ".join([ repr(item) for item in self.items ]))

class OrStatement(BaseStatement):
    @property
    def as_mongo(self):
        return {"$or": [ item.as_mongo for item in self.items ]}

    def __init__(self, string, loc, tokens):
        self.items = tokens[0][0::2]

    def __call__(self, context):
        return any([ item(context) for item in self.items ])

    def __repr__(self):
        return "({0})".format(" or ".join([ repr(item) for item in self.items ]))
