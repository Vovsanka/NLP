import sys
from heapq import heappush, heappop

from parsy import string, regex, seq

from models import SR, LR, NT, T

ESCAPE_TOKENS = {
    "(": "-LPAR-",
    ")": "-RPAR-"
}

TOKEN = regex(r"\S+").map(str)
ARROW = string("->")


syntactic_rule_parser = seq(
    TOKEN.skip(regex(r"\s+")),
    ARROW.skip(regex(r"\s+")),
    TOKEN.sep_by(regex(r"\s+"), min=2)
).map(lambda t: SR(
    label=NT(t[0]),
    child_labels=[NT(tok) for tok in t[2][:-1]],
    weight=float(t[2][-1])
))

lexical_rule_parser = seq(
    TOKEN.skip(regex(r"\s+")),   
    TOKEN.skip(regex(r"\s+")),       
    TOKEN                           
).map(lambda t: LR(
    label=NT(t[0]),
    word=T(t[1]),
    weight=float(t[2])
))


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
            rule = lexical_rule_parser.parse(line)
            rules.append(rule)
    return rules


def preprocess_raw_sentence(sentence: str) -> list[str]:
    tokens = sentence.strip().split()
    return [
        tok.replace("(", "-LRB-").replace(")", "-RRB-")
        for tok in tokens
    ]

def deduce(words: list[str], lexical_rules: list[LR], syntactic_rules: list[SR]):
    # word indices: i, j
    # NT index: k
    # rule index: r
    N = len(words)
    # 
    c: list[list[dict[int, float]]] = [[{} for _ in range(N+1)] for _ in range(N+1)]
    #
    nt_idx: dict[NT, int] = {}
    counter = 0
    for sr in lexical_rules:
        if sr.label not in nt_idx:
            nt_idx[sr.label] = counter
            counter += 1
    for sr in syntactic_rules:
        if sr.label not in nt_idx:
            nt_idx[sr.label] = counter
            counter += 1
    # 
    indexed_syntactic_rules: list[tuple] = []
    for sr in syntactic_rules:
        indexed_syntactic_rules.append((
            sr.weight, 
            nt_idx[sr.label], 
            [nt_idx[cl] for cl in sr.child_labels]
        ))
    #
    contained: list[list[int]] = [[] for _ in range(len(nt_idx))]
    for r, isr in enumerate(indexed_syntactic_rules):
        for k in isr[2]:
            contained[k].append(r)
    #
    word_set = set(words)
    word_positions: dict[str, list[int]] = {}
    for i, w in enumerate(words):
        if w not in word_positions:
            word_positions[w] = []
        word_positions[w].append(i)
    # 
    priority_queue = []
    processed: set[str] = set()
    for lr in lexical_rules:
        k = nt_idx[lr.label]
        if lr.word in word_set: 
            for i in word_positions[lr.word]:
                heappush(priority_queue, (-lr.weight, i, i + 1, k))
            processed.add(lr.word)
    if len(processed) < N:
        print(f"NOPARSE {' '.join(words)}")
        return
    # 
    while priority_queue:
        inv_w, i, j, k = heappop(priority_queue)
        if k not in c[i][j]:
            c[i][j][k] = -inv_w
            for r in contained[k]:
                ww, kk, children = indexed_syntactic_rules[r] # k in children
                if len(children) == 1: # chain rule
                    heappush(priority_queue, (ww*inv_w, i, j, kk))
                else: # len(children) == 2
                    if children[0] == k: # left child
                        for jj in range(j + 1, N):
                            if children[1] in c[j][jj]:
                                heappush(priority_queue, (ww * inv_w * c[j][jj][children[1]], i, jj, kk))
                    if children[1] == k: # right child
                        for ii in range(0, i):
                            if children[0] in c[ii][i]:
                                heappush(priority_queue, (ww * c[ii][i][children[0]] * inv_w, i, j, kk))
    # 
    print(c[0][N])

def parse_sentences(syntactic_rules_path: str, lexical_rules_path: str):
    # load grammar rules and binarize if necessary
    lexical_rules = load_lexical_rules(path=lexical_rules_path)
    syntactic_rules  = load_binarized_syntactic_rules(path=syntactic_rules_path)
    # read and parse the sentences one by one
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        words: list[str] = preprocess_raw_sentence(sentence=line)
        # deductive parsing algorithm
        deduce(
            words=words, 
            lexical_rules=lexical_rules,
            syntactic_rules=syntactic_rules
        )