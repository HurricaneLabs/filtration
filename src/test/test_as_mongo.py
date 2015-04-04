import datetime
import unittest

from nose2.tools import params
#from pyparsing import ParseException


as_mongo_tests = [
    ("symbol1", {"symbol1": {"$exists": True}}),
    ("symbol1 == 'value1'", {"symbol1": "value1"}),
    ("symbol1 != 'value1'", {"symbol1": {"$ne": "value1"}}),
    ("symbol1 < 1", {"symbol1": {"$lt": 1}}),
    ("symbol1 <= 1", {"symbol1": {"$lte": 1}}),
    ("symbol1 > 1", {"symbol1": {"$gt": 1}}),
    ("symbol1 >= 1", {"symbol1": {"$gte": 1}}),
    ("symbol1 =~ /pattern/", {"symbol1": {"$regex": "/pattern/"}}),
    ("symbol1 in 1,2", {"symbol1": {"$in": [1,2]}}),
    ("symbol1 in 127.0.0.1/32", {"symbol1": {"$in": ["127.0.0.1"]}}),
    ("symbol1 > 2014-01-01", {"symbol1": {"$gt": datetime.datetime(2014, 1, 1, 0, 0)}}),
    ("symbol1 > 12:00:00", {"symbol1": {"$gt": datetime.datetime.combine(datetime.date.today(), datetime.time(12, 0, 0))}}),
    ("not symbol1", {"$not": {"symbol1": {"$exists": True}}}),
    ("symbol1 and symbol2", {"$and": [{"symbol1": {"$exists": True}}, {"symbol2": {"$exists": True}}]}),
    ("symbol1 or symbol2", {"$or": [{"symbol1": {"$exists": True}}, {"symbol2": {"$exists": True}}]}),
]

qs_as_mongo_tests = [
    # Basic operators
    ("symbol1__eq=value", {"symbol1": "value"}),
    ("symbol1__ne=value", {"symbol1": {"$ne": "value"}}),
    ("symbol1__lt=0", {"symbol1": {"$lt": 0}}),
    ("symbol1__le=0", {"symbol1": {"$lte": 0}}),
    ("symbol1__gt=0", {"symbol1": {"$gt": 0}}),
    ("symbol1__ge=0", {"symbol1": {"$gte": 0}}),

    # Regex
    ("symbol1__contains=pattern", {"symbol1": {"$regex": "/pattern/"}}),
    ("symbol1__icontains=pattern", {"symbol1": {"$regex": "/pattern/i"}}),
    ("symbol1__startswith=pattern", {"symbol1": {"$regex": "/^pattern/"}}),
    ("symbol1__istartswith=pattern", {"symbol1": {"$regex": "/^pattern/i"}}),
    ("symbol1__endswith=pattern", {"symbol1": {"$regex": "/pattern$/"}}),
    ("symbol1__iendswith=pattern", {"symbol1": {"$regex": "/pattern$/i"}}),

#    # Dictionary expansion
    ("symbol1__key__eq=value", {"symbol1.key": "value"}),
]


class TestQsParser(unittest.TestCase):
    @params(*as_mongo_tests)
    def test_as_mongo(self, test_expr, as_mongo):
        from filtration import Expression

        expr = Expression.parseString(test_expr)
        self.assertEqual(expr.as_mongo, as_mongo)

    @params(*qs_as_mongo_tests)
    def test_qs_as_mongo(self, test_expr, as_mongo):
        from filtration import Expression

        expr = Expression.parseQsString(test_expr)
        self.assertEqual(expr.as_mongo, as_mongo)
