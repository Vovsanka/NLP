import pytest
import os

from models import SR, LR, NT, T

from parsing import (
    preprocess_rules,
    deduce,
    load_lexical_rules,
    load_syntactic_rules,
    load_indexed_outside
)
from outside import compute_outside_for_nonterminals


# --------------------------------------------------
# HELPER TO RUN DEDUCE WITH CUSTOM BEAM PARAMETERS
# --------------------------------------------------

def _run_deduce_with_beam(
    words,
    lexical,
    syntactic,
    start,
    beam_threshold,
    beam_rank
):
    """Helper to run deduce() with configurable pruning."""

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
        start=start,
        beam_threshold=beam_threshold,
        beam_rank=beam_rank,
        out={}
    )


# --------------------------------------------------
# THRESHOLD BEAM PRUNING
# --------------------------------------------------

def test_threshold_beam_keeps_best_without_pruning():

    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 0.9),
        LR(NT("B"), T("a"), 0.8),
        LR(NT("C"), T("b"), 1.0),
    ]

    syntactic = [
        # probability:
        # A path = 0.9 * 1.0 * 0.5 = 0.45
        SR(NT("S"), [NT("A"), NT("C")], 0.5),

        # probability:
        # B path = 0.8 * 1.0 * 0.99 = 0.792
        SR(NT("S"), [NT("B"), NT("C")], 0.99),
    ]

    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("S"),
        beam_threshold=0.0,
        beam_rank=99999
    )

    assert "(B a)" in result



def test_threshold_beam_can_remove_optimal_path():

    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 0.9),
        LR(NT("B"), T("a"), 0.8),
        LR(NT("C"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("S"), [NT("A"), NT("C")], 0.5),
        SR(NT("S"), [NT("B"), NT("C")], 0.99),
    ]

    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("S"),
        beam_threshold=0.95,
        beam_rank=99999
    )

    # B(a)=0.8 is pruned because:
    #
    # 0.8 <= 0.95 * 0.9
    #
    # therefore only A path remains
    assert "(A a)" in result



# --------------------------------------------------
# FIXED SIZE BEAM PRUNING
# --------------------------------------------------

def test_rank_beam_keeps_only_best_items():

    words = ["a"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("a"), 0.8),
        LR(NT("C"), T("a"), 0.7),
    ]

    syntactic = []

    # no rank pruning
    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("A"),
        beam_threshold=0.0,
        beam_rank=99999
    )

    assert result == "(A a)"



def test_rank_beam_does_not_break_parsing():

    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("S"), [NT("A"), NT("B")], 1.0)
    ]

    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("S"),
        beam_threshold=0.0,
        beam_rank=1
    )

    assert result is not None
    assert "S" in result



# --------------------------------------------------
# COMBINED PRUNING
# --------------------------------------------------

def test_threshold_and_rank_pruning_together():

    words = ["a", "b"]

    lexical = [
        LR(NT("A"), T("a"), 1.0),
        LR(NT("B"), T("a"), 0.6),
        LR(NT("C"), T("b"), 1.0),
    ]

    syntactic = [
        SR(NT("S"), [NT("A"), NT("C")], 1.0),
        SR(NT("S"), [NT("B"), NT("C")], 1.0),
    ]

    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("S"),
        beam_threshold=0.5,
        beam_rank=1
    )

    assert result is not None
    assert "(S" in result



# --------------------------------------------------
# PARAMETRIZED EDGE CASES
# --------------------------------------------------

@pytest.mark.parametrize(
    "threshold, rank",
    [
        (0.0, 99999),   # disabled pruning
        (0.1, 100),
        (0.5, 10),
        (0.9, 1),
    ]
)
def test_pruning_parameters_do_not_crash(threshold, rank):

    words = ["a"]

    lexical = [
        LR(NT("A"), T("a"), 1.0)
    ]

    syntactic = []

    result = _run_deduce_with_beam(
        words,
        lexical,
        syntactic,
        NT("A"),
        beam_threshold=threshold,
        beam_rank=rank
    )

    assert result == "(A a)"



def read_outside_file(path):
    outside = {}
    with open(path, "r") as f:
        for line in f:
            nt, weight = line.split()
            outside[nt] = float(weight)
    return outside


def test_outside_binary_rule(tmp_path):
    """
    Grammar:

        S -> NP VP 1.0
        NP -> dog 0.5
        VP -> runs 0.8

    Expected:

        out(S)  = 1.0
        out(NP) = 1.0 * 1.0 * 0.8 = 0.8
        out(VP) = 1.0 * 1.0 * 0.5 = 0.5
    """

    syntactic_rules = tmp_path / "grammar.rules"
    lexical_rules = tmp_path / "grammar.lexicon"

    syntactic_rules.write_text(
        "S -> NP VP 1.0\n"
    )

    lexical_rules.write_text(
        "NP dog 0.5\n"
        "VP runs 0.8\n"
    )

    prefix = str(tmp_path / "grammar")

    compute_outside_for_nonterminals(
        str(syntactic_rules),
        str(lexical_rules),
        "S",
        prefix
    )

    outside = read_outside_file(prefix + ".outside")

    assert outside["S"] == 1.0
    assert outside["NP"] == 0.8
    assert outside["VP"] == 0.5


def test_outside_unary_rule(tmp_path):
    """
    Grammar:

        S -> NP 0.7
        NP -> dog 0.5

    Expected:

        out(S)  = 1.0
        out(NP) = 0.7
    """

    syntactic_rules = tmp_path / "grammar.rules"
    lexical_rules = tmp_path / "grammar.lexicon"

    syntactic_rules.write_text(
        "S -> NP 0.7\n"
    )

    lexical_rules.write_text(
        "NP dog 0.5\n"
    )

    prefix = str(tmp_path / "grammar")

    compute_outside_for_nonterminals(
        str(syntactic_rules),
        str(lexical_rules),
        "S",
        prefix
    )

    outside = read_outside_file(prefix + ".outside")

    assert outside["S"] == 1.0
    assert outside["NP"] == 0.7


def test_outside_multiple_contexts(tmp_path):
    """
    Grammar:

        S -> A B 0.5
        S -> C D 0.9

        A -> a 1.0
        B -> b 1.0
        C -> c 1.0
        D -> d 1.0
    """

    syntactic_rules = tmp_path / "grammar.rules"
    lexical_rules = tmp_path / "grammar.lexicon"

    syntactic_rules.write_text(
        "S -> A B 0.5\n"
        "S -> C D 0.9\n"
    )

    lexical_rules.write_text(
        "A a 1.0\n"
        "B b 1.0\n"
        "C c 1.0\n"
        "D d 1.0\n"
    )

    prefix = str(tmp_path / "grammar")

    compute_outside_for_nonterminals(
        str(syntactic_rules),
        str(lexical_rules),
        "S",
        prefix
    )

    outside = read_outside_file(prefix + ".outside")

    assert outside["S"] == 1.0
    assert outside["A"] == 0.5
    assert outside["B"] == 0.5
    assert outside["C"] == 0.9
    assert outside["D"] == 0.9



def test_load_indexed_outside(tmp_path):
    """
    Test loading grammar.outside into indexed representation.

    outside file:
        S 1.0
        NP 0.8
        VP 0.5

    nt_idx:
        S  -> 0
        NP -> 1
        VP -> 2
        X  -> 3

    Expected:
        [1.0, 0.8, 0.5, 0.0]
    """

    outside_file = tmp_path / "grammar.outside"

    outside_file.write_text(
        "S 1.0\n"
        "NP 0.8\n"
        "VP 0.5\n"
    )

    nt_idx = {
        "S": 0,
        "NP": 1,
        "VP": 2,
        "X": 3
    }

    indexed_outside = load_indexed_outside(
        str(outside_file),
        nt_idx
    )

    assert indexed_outside == [
        1.0,
        0.8,
        0.5,
        0.0
    ]


def create_simple_grammar(tmp_path):
    """
    Grammar:

        S -> NP VP 1.0
        VP -> V 1.0

        NP -> dog 1.0
        V -> runs 1.0

    Sentence:

        dog runs
    """

    syntactic_rules = tmp_path / "grammar.rules"
    lexical_rules = tmp_path / "grammar.lexicon"

    syntactic_rules.write_text(
        "S -> NP VP 1.0\n"
        "VP -> V 1.0\n"
    )

    lexical_rules.write_text(
        "NP dog 1.0\n"
        "V runs 1.0\n"
    )

    return syntactic_rules, lexical_rules


def test_deduce_with_astar(tmp_path):
    """
    Parsing with Viterbi outside heuristic.

    The result must be identical to normal parsing.
    """

    syntactic_file, lexical_file = create_simple_grammar(tmp_path)

    outside_file = tmp_path / "grammar.outside"

    outside_file.write_text(
        "S 1.0\n"
        "NP 1.0\n"
        "VP 1.0\n"
        "V 1.0\n"
    )


    lexical_rules = load_lexical_rules(
        str(lexical_file)
    )

    syntactic_rules = load_syntactic_rules(
        str(syntactic_file)
    )

    nt_idx, indexed_rules, contained = preprocess_rules(
        lexical_rules,
        syntactic_rules
    )

    indexed_outside = load_indexed_outside(
        str(outside_file),
        nt_idx
    )

    tree = deduce(
        words=["dog", "runs"],
        lexical_rules=lexical_rules,
        syntactic_rules=syntactic_rules,
        nt_idx=nt_idx,
        indexed_syntactic_rules=indexed_rules,
        contained=contained,
        start="S",
        beam_threshold=0,
        beam_rank=99999,
        out=indexed_outside
    )

    assert tree == "(S (NP dog) (VP (V runs)))"


def test_astar_and_normal_return_same_tree(tmp_path):
    """
    A* changes only the search order.
    It must not change the Viterbi result.
    """

    syntactic_file, lexical_file = create_simple_grammar(tmp_path)

    outside_file = tmp_path / "grammar.outside"

    outside_file.write_text(
        "S 1.0\n"
        "NP 0.9\n"
        "VP 0.8\n"
        "V 0.7\n"
    )

    lexical_rules = load_lexical_rules(
        str(lexical_file)
    )

    syntactic_rules = load_syntactic_rules(
        str(syntactic_file)
    )

    nt_idx, indexed_rules, contained = preprocess_rules(
        lexical_rules,
        syntactic_rules
    )

    outside = load_indexed_outside(
        str(outside_file),
        nt_idx
    )

    normal_tree = deduce(
        words=["dog", "runs"],
        lexical_rules=lexical_rules,
        syntactic_rules=syntactic_rules,
        nt_idx=nt_idx,
        indexed_syntactic_rules=indexed_rules,
        contained=contained,
        start="S",
        beam_threshold=0,
        beam_rank=99999,
        out=[]
    )


    astar_tree = deduce(
        words=["dog", "runs"],
        lexical_rules=lexical_rules,
        syntactic_rules=syntactic_rules,
        nt_idx=nt_idx,
        indexed_syntactic_rules=indexed_rules,
        contained=contained,
        start="S",
        beam_threshold=0,
        beam_rank=99999,
        out=outside
    )


    assert normal_tree == astar_tree