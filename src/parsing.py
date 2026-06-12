import sys
from heapq import heappush, heappop

from parsy import string, regex, seq

from models import SR, LR, NT, T


TOKEN = regex(r"\S+").map(str)
ARROW = string("->")

SR_PARSER = seq(
    TOKEN.skip(regex(r"\s+")),
    ARROW.skip(regex(r"\s+")),
    TOKEN.sep_by(regex(r"\s+"), min=2)
).map(lambda t: SR(
    label=NT(t[0]),
    child_labels=[NT(tok) for tok in t[2][:-1]],
    weight=float(t[2][-1])
))

LR_PARSER = seq(
    TOKEN.skip(regex(r"\s+")),   
    TOKEN.skip(regex(r"\s+")),       
    TOKEN                           
).map(lambda t: LR(
    label=NT(t[0]),
    word=T(t[1]),
    weight=float(t[2])
))


def load_binarized_syntactic_rules(path: str) -> list[SR]:
    rules: list[SR] = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rule = SR_PARSER.parse(line)
            rules.append(rule)
    return rules


def load_lexical_rules(path: str) -> list[SR]:
    rules: list[LR] = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rule = LR_PARSER.parse(line)
            rules.append(rule)
    return rules


def deduce(words: list[str], lexical_rules: list[LR], syntactic_rules: list[SR], start: str = "ROOT") -> str:
    # word indices: i, j
    # NT index: k
    # rule index: r
    N = len(words)
    M = len(syntactic_rules)
    # 
    c: list[list[dict[int, float]]] = [[{} for _ in range(N+1)] for _ in range(N+1)]
    backtrace: list[list[dict[int, tuple[int, int, int]]]] = [[{} for _ in range(N+1)] for _ in range(N+1)]
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
    covered = [False] * N
    for r, lr in enumerate(lexical_rules):
        k = nt_idx[lr.label]
        if lr.word in word_set: 
            for i in word_positions[lr.word]:
                covered[i] = True
                heappush(priority_queue, (-lr.weight, i, i + 1, k, M + r, i + 1))
    if not all(covered):
        return f"(NOPARSE {' '.join(words)})"
    # 
    while priority_queue:
        inv_w, i, j, k, r, ij = heappop(priority_queue)
        w = -inv_w
        if k not in c[i][j] or w > c[i][j][k]:
            c[i][j][k] = w
            backtrace[i][j][k] = (r, ij)
            for rr in contained[k]:
                ww, kk, children = indexed_syntactic_rules[rr] # k in children
                if len(children) == 1: # chain rule
                    heappush(priority_queue, (ww*inv_w, i, j, kk, rr, j))
                else: # len(children) == 2
                    if children[0] == k: # left child
                        for jj in range(j + 1, N + 1):
                            if children[1] in c[j][jj]:
                                heappush(priority_queue, (ww * inv_w * c[j][jj][children[1]], i, jj, kk, rr, j))
                    if children[1] == k: # right child
                        for ii in range(0, i):
                            if children[0] in c[ii][i]:
                                heappush(priority_queue, (ww * c[ii][i][children[0]] * inv_w, ii, j, kk, rr, i))
    # 
    if nt_idx[start] not in c[0][N]:
        return f"(NOPARSE {' '.join(words)})"
    #
    r, ij = backtrace[0][N][nt_idx[start]]
    stack = [(r, 0, ij, N)] 
    close_stack = []
    ptb = ""
    while stack:
        r, i, ij, j = stack.pop()
        if r >= M: # i + 1 == j
            lr = lexical_rules[r - M]
            ptb += f"({lr.label} {lr.word})"
            while close_stack and close_stack[-1] == j:
                _ = close_stack.pop()
                ptb += ")"
            ptb += " "
            continue
        sr = syntactic_rules[r]
        ptb += f"({sr.label} "
        close_stack.append(j)
        if ij != j:  # not chain rule
            r2, ij2 = backtrace[ij][j][nt_idx[sr.child_labels[1]]]
            stack.append((r2, ij, ij2, j))
        r1, ij1 = backtrace[i][ij][nt_idx[sr.child_labels[0]]]
        stack.append((r1, i, ij1, ij)) 
    return ptb.rstrip()

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
        words: list[str] = line.strip().split()
        # deductive parsing algorithm
        print(deduce(
            words=words, 
            lexical_rules=lexical_rules,
            syntactic_rules=syntactic_rules
        ))