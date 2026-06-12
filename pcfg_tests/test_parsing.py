import pytest

from parsing import (
    SR_PARSER,
    LR_PARSER,
    load_binarized_syntactic_rules,
    load_lexical_rules,
    deduce,
)

from models import SR, LR, NT, T


# -------------------------
# SR PARSER TEST
# -------------------------
def test_sr_parser():
    line = "S -> A B 0.75"
    sr = SR_PARSER.parse(line)

    assert sr.label == NT("S")
    assert sr.child_labels == [NT("A"), NT("B")]
    assert sr.weight == 0.75


# -------------------------
# LR PARSER TEST
# -------------------------
def test_lr_parser():
    line = "A a 0.9"
    lr = LR_PARSER.parse(line)

    assert lr.label == NT("A")
    assert lr.word == T("a")
    assert lr.weight == 0.9


# -------------------------
# LOAD SYNTACTIC RULES
# -------------------------
def test_load_syntactic_rules(tmp_path):
    f = tmp_path / "rules.txt"
    f.write_text("S -> A B 1.0\nX -> S C 0.5\n")

    rules = load_binarized_syntactic_rules(str(f))

    assert len(rules) == 2
    assert rules[0].label == NT("S")
    assert rules[1].label == NT("X")


# -------------------------
# LOAD LEXICAL RULES
# -------------------------
def test_load_lexical_rules(tmp_path):
    f = tmp_path / "lex.txt"
    f.write_text("A a 0.9\nB b 0.8\n")

    rules = load_lexical_rules(str(f))

    assert len(rules) == 2
    assert rules[0].word == T("a")
    assert rules[1].word == T("b")


# -------------------------
# SINGLE WORD PARSE
# -------------------------
def test_deduce_single_word():
    words = ["a"]

    lexical = [
        LR(NT("A"), T("a"), 1.0)
    ]
    syntactic = []

    out = deduce(words, lexical, syntactic, start="A")

    assert "(A a)" in out


# -------------------------
# NOPARSE CASE
# -------------------------
def test_deduce_noparse():
    words = ["a"]

    lexical = [
        LR(NT("A"), T("b"), 1.0)
    ]
    syntactic = []

    out = deduce(words, lexical, syntactic, start="A")

    assert out.startswith("(NOPARSE")


# -------------------------
# BINARY TREE PARSE
# -------------------------
def test_deduce_binary_tree():
    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("S"), [NT("A"), NT("B")], 1.0)
    ]

    out = deduce(words, lexical, syntactic, start="S")

    assert "S" in out
    assert "a" in out
    assert "b" in out


# -------------------------
# START SYMBOL OVERRIDE
# -------------------------
def test_start_symbol_override():
    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("X"), [NT("A"), NT("B")], 1.0)
    ]

    out = deduce(words, lexical, syntactic, start="X")

    assert "(X" in out


# -------------------------
# PTB FORMATTING CHECK
# -------------------------
def test_ptb_formatting():
    words = ["a"]

    lexical = [
        LR(NT("A"), T("a"), 1.0)
    ]

    out = deduce(words, lexical, [], start="A")

    assert out.endswith(")")
    assert not out.endswith(" ")


# -------------------------
# INTEGRATION TEST
# -------------------------
def test_full_pipeline():
    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("S"), [NT("A"), NT("B")], 1.0)
    ]

    out = deduce(words, lexical, syntactic, start="S")

    assert "S" in out
    assert "a" in out
    assert "b" in out