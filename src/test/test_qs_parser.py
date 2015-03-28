# Basic operators
("symbol__eq=value", "symbol == 'value'"),
("symbol__ne=value", "symbol != 'value'"),
("symbol__lt=int", "symbol < int"),
("symbol__le=int", "symbol <= int"),
("symbol__gt=int", "symbol > int"),
("symbol__ge=int", "symbol >= int"),

# Regex
("symbol__contains=pattern", "symbol =~ /pattern/"),
("symbol__icontains=pattern", "symbol =~ /pattern/i"),

# Dictionary expansion
("symbol__key__eq=value", "symbol.key == 'value'"),
