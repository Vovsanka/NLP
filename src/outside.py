import sys

from models import SR, LR, NT, T
from parsing import load_lexical_rules, load_syntactic_rules


def compute_outside_for_nonterminals(
    syntactic_rules_path: str, 
    lexical_rules_path: str, 
    start_symbol: str,
    grammar_prefix: str|None = None
):
    lexical_rules: list[LR] = load_lexical_rules(path=lexical_rules_path)
    syntactic_rules: list[SR]  = load_syntactic_rules(path=syntactic_rules_path)
    #
    nonterminals: set[NT] = set()
    for sr in syntactic_rules:
        nonterminals.add(sr.label)
        for child in sr.child_labels:
            nonterminals.add(child)
    for lr in lexical_rules:
        nonterminals.add(lr.label)
    #
    inside: dict[NT, float] = {
        nt: 0.0 for nt in nonterminals
    }
    #
    for lr in lexical_rules:
        inside[lr.label] = max(
            inside[lr.label],
            lr.weight
        )
    #
    changed = True
    while changed:
        changed = False
        for sr in syntactic_rules:
            A = sr.label

            if len(sr.child_labels) == 2:
                B, C = sr.child_labels
                candidate = (
                    sr.weight
                    * inside[B]
                    * inside[C]
                )

            elif len(sr.child_labels) == 1:
                B = sr.child_labels[0]
                candidate = (
                    sr.weight
                    * inside[B]
                )

            else:
                raise ValueError(
                    f"Grammar is not binarized: {sr}"
                )

            if candidate > inside[A] + 1e-12:
                inside[A] = candidate
                changed = True
    #
    outside: dict[NT, float] = {
        nt: 0.0 for nt in nonterminals
    }
    outside[start_symbol] = 1.0
    #
    changed = True
    while changed:
        changed = False

        for sr in syntactic_rules:
            A = sr.label

            if outside[A] == 0.0:
                continue

            if len(sr.child_labels) == 2:
                B, C = sr.child_labels

                # A -> B C
                candidate = (
                    outside[A]
                    * sr.weight
                    * inside[C]
                )

                if candidate > outside[B] + 1e-12:
                    outside[B] = candidate
                    changed = True

                # A -> C B
                candidate = (
                    outside[A]
                    * sr.weight
                    * inside[B]
                )

                if candidate > outside[C] + 1e-12:
                    outside[C] = candidate
                    changed = True

            elif len(sr.child_labels) == 1:
                B = sr.child_labels[0]

                # A -> B
                candidate = (
                    outside[A]
                    * sr.weight
                )

                if candidate > outside[B] + 1e-12:
                    outside[B] = candidate
                    changed = True

            else:
                raise ValueError(
                    f"Grammar is not binarized: {sr}"
                )
    #
    if grammar_prefix is None:
        outside_f = sys.stdout
    else:
        outside_f = open(grammar_prefix + ".outside", "w")
    #
    for nt, weight in outside.items():
        if weight > 0:
            print(nt, weight, file=outside_f)
    #
    if grammar_prefix is None:
        sys.stdout.flush()
    else:
        outside_f.close()