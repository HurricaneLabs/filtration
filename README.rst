##########
Filtration
##########

**A library for parsing arbitrary filters provided by a UI or as a Query String**

Features
========
- Compatible with Python 3
- Parses human readable filters

Get Filtration
==============

.. code-block:: shell

    pip install git+https://github.com/HurricaneLabs/filtration.git

Run the tests
=============
You must install nose2, then run:

.. code-block:: shell

    git clone https://github.com/HurricaneLabs/filtration.git
    cd filtration
    nose2

########
Usage
########
Filtration is used to parse "filter expressions" made up of one or more "statements". Each
statement is comprised of a "left hand side" (LHS), and optionally an operator and a "right hand
side" (RHS). When no operator and RHS are specified, a special "LHS exists" syntax is assumed. See
"Expression Evaluation" for more details.

Statements are joined together using "AND" or "OR" to form an expression. Parentheses may be used
when joining statements together to enforce precedence. For example:

.. code-block:: python

    >>> from filtration import Expression
    >>> Expression.parseString("a and b or c")
    ((a and b) or c)
    >>> Expression.parseString("a and (b or c)")
    (a and (b or c))
    >>>

Filtration can also be used to parse query string syntax. See below for more information.

Expression Format
=================

Operators
~~~~~~~~~
These operators control comparison of the LHS to the RHS. If the operator is omitted (and thus
the RHS is also omitted), the statement returns True IF the symbol in the LHS exists at all.

* Equal ("==")
* Not equal ("!=")
* Less than ("<")
* Less than or equal ("<=")
* Greater than (">")
* Greater than or equal (">=")
* Contains ("in")
    * RHS must be a list or a Subnet
* Regular expression ("=~")
    * RHS must be a regex token

Tokens
~~~~~~~~~~~~~~~
These tokens are used in the LHS or RHS of a statement.

Regex
-----
A regular expression must be wrapped in "/" and may contain the characters "i", "m" or "s" after
the closing "/" to represent the corresponding regex flags. Examples::

    /abc/
    /^abc/i
    /^abc$/ms

Subnet
------
A subnet is an IPv4 subnet in CIDR notation::

    127.0.0.0/8
    192.168.0.0/24

Symbol
------
A symbol is represented as a bare, unquoted string. It begins with a letter or underscore, and
can be followed by any number of letters, numbers, dots (".") or underscores. Dots have special
meaning and are used to indicate dictionary traversal (see Expression Evaluation below).

Value
-----
A value can be a date, time, date/time, quoted string, or an integer. A date is represented in
YYYY-MM-DD format (not quoted), and is interpreted to mean midnight on that date. A time is
represented in HH:MM:SS format (also not quoted), and is interpreted to mean that time on whatever
day the filter is evaluated. A date/time is represented in YYYY-MM-DDTHH:MM:SS format, where the
"T" is optional and could instead be represented by a space. This format is roughly ISO 8601, but
is lacking microseconds.

List
----
A list is two-or-more Value tokens separated by commas.

Expression Evaluation
=====================

Expression objects are callable, with a single "context" argument. When used in this way, either
true or false is returned, based on whether the "context" matches the filter. For example, given
this context:

.. code-block:: python

    >>> c = {"a": 1, "b": 2, "c": 3}

and this expression:

.. code-block:: python

    >>> expr = Expression.parseString("a == 1 and b == 2")

calling the expression would return True:

.. code-block:: python

    >>> expr(c)
    True
    >>>

whereas this expression would return False:

.. code-block:: python

    >>> expr = Expression.parseString("a == 2 and b == 2")
    >>> expr(c)
    False
    >>>

When no operator/RHS is provided, the statement resolves to true if the LHS key exists in the
context. For example:

.. code-block:: python

    >>> c = {"a": 1, "b": 2, "c": 3}
    >>> expr = Expression.parseString("a")
    >>> expr(c)
    True
    >>> expr = Expression.parseString("d")
    >>> expr(c)
    False
    >>>

Dictionary Traversal
~~~~~~~~~~~~~~~~~~~~

Symbols are able to traverse nested dictionaries in the context. Given this context:

.. code-block:: python

    >>> c = {"a": {"b": {"c": 1}}}

This expression will return true:

.. code-block:: python

    >>> expr = Expression.parseString("a.b.c == 1")
    >>> expr(c)
    True
    >>>
