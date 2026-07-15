import pytest

from parsing import (
    preprocess_rules,
    deduce,
)

from models import SR, LR, NT, T


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
        beam_rank=beam_rank
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