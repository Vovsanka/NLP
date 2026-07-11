import pytest

from parsing import (
    SR_PARSER,
    LR_PARSER,
    load_binarized_syntactic_rules,
    load_lexical_rules,
    preprocess_rules,
    deduce,
)

from models import SR, LR, NT, T


# -------------------------
# HELPER TO RUN DEDUCE WITH PREPROCESSING
# -------------------------
def _run_deduce(words, lexical, syntactic, start):
    """Helper to handle the preprocessing requirements of deduce()"""
    nt_idx, indexed_syntactic_rules, contained = preprocess_rules(
        lexical_rules=lexical, 
        syntactic_rules=syntactic
    )
    return deduce(
        words=words,
        lexical_rules=lexical,
        syntactic_rules=syntactic,
        nt_idx=nt_idx,
        indexed_syntactic_rules=indexed_syntactic_rules,
        contained=contained,
        start=start
    )


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

    out = _run_deduce(words, lexical, syntactic, start=NT("A"))

    assert "(A a)" in out


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

    out = _run_deduce(words, lexical, syntactic, start=NT("S"))

    assert "S" in out
    assert "a" in out
    assert "b" in out


# -------------------------
# CHAIN RULE PARSE
# -------------------------
def test_deduce_chain_rule():
    words = ["a"]

    lexical = [
        LR(NT("B"), T("a"), 1.0)
    ]
    # S -> B (Chain rule parsing branch where len(children) == 1)
    syntactic = [
        SR(NT("S"), [NT("B")], 0.9)
    ]

    out = _run_deduce(words, lexical, syntactic, start=NT("S"))

    assert "(S (B a))" in out


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

    out = _run_deduce(words, lexical, syntactic, start=NT("X"))

    assert "(X" in out


# -------------------------
# PTB FORMATTING CHECK
# -------------------------
def test_ptb_formatting():
    words = ["a"]

    lexical = [
        LR(NT("A"), T("a"), 1.0)
    ]

    out = _run_deduce(words, lexical, [], start=NT("A"))

    assert out.endswith(")")
    assert not out.endswith(" ")


# -------------------------
# OOV NOPARSE (Out of Vocabulary Error)
# -------------------------
def test_deduce_oov_noparse():
    words = ["a", "unknown_word"]

    lexical = [
        LR(NT("A"), T("a"), 1.0)
    ]
    syntactic = []

    out = _run_deduce(words, lexical, syntactic, start=NT("A"))

    assert out == "(NOPARSE a unknown_word)"


# -------------------------
# STRUCTURAL NOPARSE (Words known, but rules don't form a valid tree)
# -------------------------
def test_deduce_structural_noparse():
    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("b"), 1.0),
        LR(NT("C"), T("dummy"), 1.0)  # Registers 'C' in nt_idx so preprocessing doesn't KeyError
    ]
    # S -> A C cannot parse "a b" because "b" is a B, not a C.
    syntactic = [
        SR(NT("S"), [NT("A"), NT("C")], 1.0)
    ]

    out = _run_deduce(words, lexical, syntactic, start=NT("S"))

    assert out == "(NOPARSE a b)"


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

    out = _run_deduce(words, lexical, syntactic, start=NT("S"))

    assert "S" in out
    assert "a" in out
    assert "b" in out