import io
import sys

from unking import unk_trees   # adapt import to your filename


# -------------------------
# BASIC UNKING
# -------------------------
def test_unk_single_rare_word(monkeypatch, capsys):
    treebank = """
(S (NP (NN dog)))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=1)

    output = capsys.readouterr().out.strip()

    assert "(NN UNK)" in output
    assert "dog" not in output


# -------------------------
# FREQUENT WORDS ARE KEPT
# -------------------------
def test_unk_keeps_frequent_words(monkeypatch, capsys):
    treebank = """
(S (NN dog))
(S (NN dog))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=1)

    output = capsys.readouterr().out.strip().splitlines()

    assert "(NN dog)" in output[0]
    assert "(NN dog)" in output[1]
    assert "UNK" not in output[0]
    assert "UNK" not in output[1]


# -------------------------
# RARE WORDS ARE REPLACED, FREQUENT WORDS ARE NOT
# -------------------------
def test_unk_mixed_frequency(monkeypatch, capsys):
    treebank = """
(S (NN dog))
(S (NN dog))
(S (NN cat))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=1)

    output = capsys.readouterr().out

    # dog occurs twice -> stays
    assert "(NN dog)" in output

    # cat occurs once -> UNK
    assert "(NN UNK)" in output
    assert "(NN cat)" not in output


# -------------------------
# MULTIPLE RARE WORDS
# -------------------------
def test_unk_multiple_rare_words(monkeypatch, capsys):
    treebank = """
(S (NN cat) (VB runs))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=1)

    output = capsys.readouterr().out.strip()

    assert "(NN UNK)" in output
    assert "(VB UNK)" in output


# -------------------------
# TREE STRUCTURE IS PRESERVED
# -------------------------
def test_unk_preserves_structure(monkeypatch, capsys):
    treebank = """
(ROOT (NP (DT the) (NN dog)) (VP (VB runs)))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=1)

    output = capsys.readouterr().out.strip()

    assert output.startswith("(ROOT")
    assert "(NP" in output
    assert "(VP" in output
    assert output.count("UNK") == 3


# -------------------------
# THRESHOLD ZERO DOES NOT REPLACE WORDS
# -------------------------
def test_unk_threshold_zero(monkeypatch, capsys):
    treebank = """
(S (NN dog))
"""

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(treebank.strip())
    )

    unk_trees(threshold=0)

    output = capsys.readouterr().out.strip()

    assert "(NN dog)" in output
    assert "UNK" not in output


# -------------------------
# SMOOTHING: SINGLE RARE WORD
# -------------------------
def test_unk_smoothing_single_word(monkeypatch, capsys):
    treebank = """
(S (NN dog))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=1, smoothing=True)
    output = capsys.readouterr().out.strip()

    # dog → len=3 → UNK-L
    assert "(NN UNK-L)" in output
    assert "dog" not in output


# -------------------------
# SMOOTHING: FREQUENT WORDS ARE KEPT
# -------------------------
def test_unk_smoothing_keeps_frequent(monkeypatch, capsys):
    treebank = """
(S (NN dog))
(S (NN dog))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=1, smoothing=True)
    output = capsys.readouterr().out.strip().splitlines()

    assert "(NN dog)" in output[0]
    assert "(NN dog)" in output[1]
    assert "UNK" not in output[0]
    assert "UNK" not in output[1]


# -------------------------
# SMOOTHING: MIXED FREQUENCY
# -------------------------
def test_unk_smoothing_mixed(monkeypatch, capsys):
    treebank = """
(S (NN dog))
(S (NN dog))
(S (NN cat))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=1, smoothing=True)
    output = capsys.readouterr().out

    # dog occurs twice → kept
    assert "(NN dog)" in output

    # cat → len=3 → UNK-L
    assert "(NN UNK-L)" in output
    assert "(NN cat)" not in output


# -------------------------
# SMOOTHING: MULTIPLE RARE WORDS
# -------------------------
def test_unk_smoothing_multiple_rare(monkeypatch, capsys):
    treebank = """
(S (NN cat) (VB runs))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=1, smoothing=True)
    output = capsys.readouterr().out.strip()

    # cat → len=3 → UNK-L
    assert "(NN UNK-L)" in output

    # runs → len=4 → UNK-L-s
    assert "(VB UNK-L-s)" in output


# -------------------------
# SMOOTHING: STRUCTURE PRESERVED
# -------------------------
def test_unk_smoothing_preserves_structure(monkeypatch, capsys):
    treebank = """
(ROOT (NP (DT the) (NN dog)) (VP (VB runs)))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=1, smoothing=True)
    output = capsys.readouterr().out.strip()

    assert output.startswith("(ROOT")
    assert "(NP" in output
    assert "(VP" in output

    # the → len=3 → UNK-L
    # dog → len=3 → UNK-L
    # runs → len=4 → UNK-L-s
    assert output.count("UNK") == 3


# -------------------------
# SMOOTHING: THRESHOLD ZERO → NO UNKING
# -------------------------
def test_unk_smoothing_threshold_zero(monkeypatch, capsys):
    treebank = """
(S (NN dog))
"""
    monkeypatch.setattr(sys, "stdin", io.StringIO(treebank.strip()))
    unk_trees(threshold=0, smoothing=True)
    output = capsys.readouterr().out.strip()

    assert "(NN dog)" in output
    assert "UNK" not in output
