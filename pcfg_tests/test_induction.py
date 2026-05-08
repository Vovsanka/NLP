import io
import sys
import os
import pytest

from induction import parse_ptb, induce_grammar


def run_induction(input_text: str, prefix=None) -> str:
    backup_stdin = sys.stdin
    backup_stdout = sys.stdout

    sys.stdin = io.StringIO(input_text)
    sys.stdout = io.StringIO()

    induce_grammar(prefix)

    output = sys.stdout.getvalue()

    sys.stdin = backup_stdin
    sys.stdout = backup_stdout

    return output


def test_parse_ptb_simple():
    se = parse_ptb("(A (B b))")
    assert se.label == "A"
    assert len(se.children) == 1
    assert se.children[0].label == "B"
    assert se.children[0].children[0] == "b"


def test_parse_ptb_raises_on_extra_content():
    with pytest.raises(Exception):
        parse_ptb("(A a) garbage")


def test_roundtrip_str_se_equals_input():
    line = "(A (B b))"
    se = parse_ptb(line)
    assert str(se) == line


def test_single_rule_and_lexicon():
    out = run_induction("(A (B b))\n")

    assert "A -> B 1" in out
    assert "B b 1" in out
    assert "b" in out


def test_multiple_lexical_probabilities():
    out = run_induction("(A a)\n(A b)\n(A a)\n")

    lexicon_section = out.split("Grammar.lexicon:")[-1]
    assert "->" not in lexicon_section

    assert "A a" in out
    assert "A b" in out

    assert "a" in out
    assert "b" in out


def test_stops_on_empty_line():
    out = run_induction("(A a)\n(A b)\n\n(A c)\n")

    assert "A a" in out
    assert "A b" in out
    assert "A c" not in out


def test_nested_structure_rules():
    out = run_induction("(S (NP (N dog)) (VP (V runs)))\n")

    assert "S -> NP VP" in out
    assert "NP -> N" in out
    assert "VP -> V" in out

    assert "N dog" in out
    assert "V runs" in out

    assert "dog" in out
    assert "runs" in out


def test_probability_normalization_with_mixed_rules():
    out = run_induction(
        # A expands 3 times: 2×B, 1×C
        "(A (B b))\n"
        "(A (B (C c)))\n"
        "(A (C c))\n"
    )

    # --- A rules ---
    # A -> B occurs twice
    # A -> C occurs once
    assert "A -> B 0.666"[:10] in out or "A -> B 0.667"[:10] in out
    assert "A -> C 0.333"[:10] in out

    # --- B rules ---
    # B appears twice:
    #   1× lexical: B -> b
    #   1× syntactic: B -> C
    #
    # So:
    #   P(B -> b) = 1/2
    #   P(B -> C) = 1/2

    # lexical
    assert "B b 0.5" in out or "B b 0.50" in out

    # syntactic
    assert "B -> C 0.5" in out or "B -> C 0.50" in out

    # --- C rules ---
    # C appears twice:
    #   2× lexical: C -> c
    assert "C c 1" in out

    # --- words ---
    assert "b" in out
    assert "c" in out


def test_writes_grammar_files(tmp_path):
    prefix = tmp_path / "grammar"

    run_induction("(A (B b))\n", prefix=str(prefix))

    rules_file = prefix.with_suffix(".rules")
    lex_file = prefix.with_suffix(".lexicon")
    words_file = prefix.with_suffix(".words")

    assert rules_file.exists()
    assert lex_file.exists()
    assert words_file.exists()

    assert "A -> B 1" in rules_file.read_text()
    assert "B b 1" in lex_file.read_text()
    assert "b" in words_file.read_text()
