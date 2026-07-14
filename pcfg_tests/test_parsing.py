import sys
import io
from parsing import parse_sentences
from parsing import (
    SR_PARSER,
    LR_PARSER,
    load_syntactic_rules,
    load_lexical_rules,
    preprocess_rules,
    deduce,
    parse_sentences
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

    rules = load_syntactic_rules(str(f))

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

    assert out is None


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

    assert out is None


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


# -------------------------
# UNKING: UNKNOWN WORD FAILS WITHOUT -u
# -------------------------
def test_parse_sentence_unknown_word_without_unking(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    lexicon.write_text(
        "A known 1.0\n"
    )

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("unknown\n")
    )

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=False,
        smoothing=False
    )

    output = capsys.readouterr().out.strip()

    assert output == "(NOPARSE unknown)"


# -------------------------
# UNKING: UNKNOWN WORD IS REPLACED BY UNK
# -------------------------
def test_parse_sentence_unknown_word_with_unking(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")

    # The important part: grammar contains UNK
    lexicon.write_text(
        "A UNK 1.0\n"
    )

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("unknown\n")
    )

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=False
    )

    output = capsys.readouterr().out.strip()

    # UNK should be restored to the original word
    assert output == "(A unknown)"


# -------------------------
# UNKING: KNOWN WORD IS NOT REPLACED
# -------------------------
def test_parse_sentence_known_word_not_unked(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")

    lexicon.write_text(
        "A known 1.0\n"
        "A UNK 1.0\n"
    )

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("known\n")
    )

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=False
    )

    output = capsys.readouterr().out.strip()

    assert output == "(A known)"
    assert "UNK" not in output


# -------------------------
# UNKING: MIXED KNOWN AND UNKNOWN WORDS
# -------------------------
def test_parse_sentence_mixed_known_unknown_with_unking(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text(
        "S -> A B 1.0\n"
    )

    lexicon.write_text(
        "A known 1.0\n"
        "B UNK 1.0\n"
    )

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("known unknown\n")
    )

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="S",
        unking=True,
        smoothing=False
    )

    output = capsys.readouterr().out.strip()

    assert "known" in output
    assert "unknown" in output
    assert "UNK" not in output


# -------------------------
# UNKING: MULTIPLE UNKNOWN WORDS
# -------------------------
def test_parse_sentence_multiple_unknown_words_with_unking(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text(
        "S -> A B 1.0\n"
    )

    lexicon.write_text(
        "A UNK 1.0\n"
        "B UNK 1.0\n"
    )

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("first second\n")
    )

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="S",
        unking=True,
        smoothing=False
    )

    output = capsys.readouterr().out.strip()

    assert "first" in output
    assert "second" in output
    assert "UNK" not in output


# -------------------------
# UNKING + SMOOTHING: UNKNOWN WORD → SIGNATURE
# -------------------------
def test_parse_sentence_unknown_word_with_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # x9 → lowercase + digit → UNK-L-n
    lexicon.write_text("A UNK-L-n 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("x9\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A x9)"


# -------------------------
# UNKING + SMOOTHING: SENTENCE-INITIAL CAPITALIZED → UNK-C-o
# -------------------------
def test_parse_sentence_initial_capitalized_with_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # Hello → UNK-C-o (because i=0, so SC is NOT triggered)
    lexicon.write_text("A UNK-C-o 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("Hello\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A Hello)"


# -------------------------
# UNKING + SMOOTHING: LOWERCASE WORD → UNK-L-o
# -------------------------
def test_parse_sentence_lowercase_with_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # piano → ends with 'o' → UNK-L-o
    lexicon.write_text("A UNK-L-o 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("piano\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A piano)"


# -------------------------
# UNKING + SMOOTHING: MULTIPLE UNKNOWN WORDS → DIFFERENT SIGNATURES
# -------------------------
def test_parse_sentence_multiple_unknown_words_with_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("S -> A B 1.0\n")

    # Hello → UNK-C-o
    # windy → UNK-L-y
    lexicon.write_text(
        "A UNK-C-o 1.0\n"
        "B UNK-L-y 1.0\n"
    )

    monkeypatch.setattr(sys, "stdin", io.StringIO("Hello windy\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="S",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()

    assert "Hello" in output
    assert "windy" in output
    assert "UNK" not in output


# -------------------------
# UNKING + SMOOTHING: PERIOD → UNK-L-P
# -------------------------
def test_parse_sentence_unknown_with_period_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # u.s.a. → UNK-L-P
    lexicon.write_text("A UNK-L-P 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("u.s.a.\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A u.s.a.)"


# -------------------------
# UNKING + SMOOTHING: COMMA → UNK-L-C
# -------------------------
def test_parse_sentence_unknown_with_comma_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # hello, → UNK-L-C
    lexicon.write_text("A UNK-L-C 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("hello,\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A hello,)"


# -------------------------
# UNKING + SMOOTHING: DASH → UNK-L-H-y
# -------------------------
def test_parse_sentence_unknown_with_dash_smoothing(tmp_path, monkeypatch, capsys):
    rules = tmp_path / "rules"
    lexicon = tmp_path / "lexicon"

    rules.write_text("")
    # high-quality → UNK-L-H-y
    lexicon.write_text("A UNK-L-H-y 1.0\n")

    monkeypatch.setattr(sys, "stdin", io.StringIO("high-quality\n"))

    parse_sentences(
        syntactic_rules_path=str(rules),
        lexical_rules_path=str(lexicon),
        start_symbol="A",
        unking=True,
        smoothing=True
    )

    output = capsys.readouterr().out.strip()
    assert output == "(A high-quality)"
