import pytest
from models import SE, SR, LR, NT, T


def test_symbolic_expression_terminal_child():
    se = SE("A", ["a"])
    assert se.label == "A"
    assert se.children == ["a"]
    assert str(se) == "(A a)"


def test_symbolic_expression_nonterminal_children():
    child = SE("B", ["b"])
    parent = SE("A", [child])
    assert parent.label == "A"
    assert isinstance(parent.children[0], SE)
    assert str(parent) == "(A (B b))"


def test_symbolic_expression_invalid_terminal_mixed_children():
    with pytest.raises(Exception):
        SE("A", ["a", SE("B", ["b"])])


def test_syntactic_rule_equality_and_hash():
    r1 = SR("A", ["B", "C"])
    r2 = SR("A", ["B", "C"])
    r3 = SR("A", ["C", "B"])
    assert r1 == r2
    assert r1 != r3
    assert hash(r1) == hash(r2)


def test_lexical_rule_equality_and_hash():
    r1 = LR("A", "a")
    r2 = LR("A", "a")
    r3 = LR("A", "b")
    assert r1 == r2
    assert r1 != r3
    assert hash(r1) == hash(r2)
