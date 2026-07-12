import pytest

from binarization import binarise_one_tree
from induction import parse_ptb


def binarise(tree: str, H: int, V: int):
    se = parse_ptb(tree=tree)
    return str(binarise_one_tree(se, H, V))


def test_preterminal_unchanged():
    tree = "(NN dog)"

    result = binarise(tree, H=2, V=2)

    assert result == "(NN dog)"


def test_binary_tree_unchanged():
    tree = "(NP (DT the) (NN dog))"

    result = binarise(tree, H=2, V=2)

    assert result == "(NP^<TOP> (DT the) (NN dog))" or "NP" in result


def test_left_binarisation_three_children():
    tree = "(NP (DT the) (JJ big) (NN dog))"

    result = binarise(tree, H=2, V=1)

    # should introduce artificial node
    assert "|<" in result

    # left child remains first child
    assert "(DT the)" in result


def test_vertical_markovization_v1():
    tree = "(S (NP (DT the) (NN dog)) (VP (V runs)))"

    result = binarise(tree, H=2, V=1)

    # V=1 means no parent annotation
    assert "^<" not in result


def test_vertical_markovization_v2():
    tree = "(S (NP (DT the) (NN dog)) (VP (V runs)))"

    result = binarise(tree, H=2, V=2)

    # child nodes should contain one ancestor
    assert "^<S>" in result or "^<NP>" in result


def test_horizontal_markovization_h1():
    tree = "(A (B b) (C c) (D d) (E e))"

    result = binarise(tree, H=1, V=1)

    # artificial node remembers only one sibling
    assert "|<C>" in result

    # should not remember all siblings
    assert "|<C,D,E>" not in result


def test_horizontal_markovization_h2():
    tree = "(A (B b) (C c) (D d) (E e))"

    result = binarise(tree, H=2, V=1)

    assert "|<C,D>" in result


def test_horizontal_markovization_infinity():
    tree = "(A (B b) (C c) (D d) (E e))"

    result = binarise(tree, H=100, V=1)

    assert "|<C,D,E>" in result


def test_artificial_nodes_do_not_get_new_vertical_context():
    tree = "(S (A a) (B b) (C c))"

    result = binarise(tree, H=2, V=3)

    # artificial nodes should not receive S as ancestor
    # (they inherit original ancestors)
    assert "|<B,C>" in result