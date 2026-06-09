import sys

from parsy import string, regex, seq

from models import SR, LR, NT, T

ESCAPE_TOKENS = {
    "(": "-LPAR-",
    ")": "-RPAR-",
    " ": "_"
}

nonterminal = regex(r"\S+").map(NT)
terminal    = regex(r"\S+").map(T)
literal     = regex(r"\S+")           
arrow       = string("->")
weight      = regex(r"[0-9]*\.?[0-9]+").map(float)

syntactic_rule_parser = seq(
    nonterminal.skip(regex(r"\s+")),
    arrow.skip(regex(r"\s+")),
    nonterminal.sep_by(regex(r"\s+"), min=1),
    regex(r"\s+") >> weight
).map(lambda t: SR(t[0], t[1], t[2]))

lexical_rule_parser = seq(
    nonterminal.skip(regex(r"\s+")),   
    literal.skip(regex(r"\s+")),       
    terminal                           
).map(lambda t: LR(t[0], t[1], t[2]))



def load_binarized_syntactic_rules(path: str) -> list[SR]:
    bin_rules: list[SR] = []
    nt_counter: dict[NT, int] = {}
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rule = syntactic_rule_parser.parse(line)
            if len(rule.child_labels) <= 2:
                bin_rules.append(rule)
                continue
            # binarization (=> CNF)
            if rule.label not in nt_counter:
                nt_counter[rule.label] = 0
            current_label = rule.label
            for i in range(len(rule.child_labels) - 1):
                if i == len(rule.child_labels) - 2:
                    next_label = rule.child_labels[-1]
                else:
                    nt_counter[rule.label] += 1
                    next_label = NT(f"{rule.label}@{nt_counter[rule.label]}")
                bin_rules.append(SR(
                    label=current_label,
                    child_labels=[
                        rule.child_labels[i],
                        next_label
                    ],
                    weight=rule.weight if i == 0 else 1.0
                ))
                current_label = next_label
    return bin_rules


def load_lexical_rules(path: str) -> list[SR]:
    rules: list[LR] = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rule = syntactic_rule_parser.parse(line)
            rules.append(rule)
    return rules


def parse_sentences(syntactic_rules_path: str, lexical_rules_path: str):
    # load and binarize grammar rules 
    syntactic_rules  = load_binarized_syntactic_rules(path=syntactic_rules_path)
    lexical_rules = load_lexical_rules(path=lexical_rules_path)
    print(syntactic_rules)
    # read and parse the sentences one by one
    # for line in sys.stdin:
    #     # read the line with the tree from stdin
    #     line = line.rstrip("\n")
    #     if not line.strip():
    #         break  # finish if reached an empty line (or enter pressed)
    #     sentence = preprocess_raw_sentence(sentence=line)
    #     # TODO: implement a parsing algorithm (CYK or deductive? think of datastructures for the rules)