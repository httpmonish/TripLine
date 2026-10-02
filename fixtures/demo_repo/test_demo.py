import pytest
from math_ops import add
from string_ops import to_upper
from dict_ops import safe_lookup

def test_issue_1():
    assert add(2, 3) == 5

def test_issue_2():
    assert to_upper("hello") == "HELLO"

def test_issue_3():
    assert safe_lookup({"a": 1}, "b") is None
