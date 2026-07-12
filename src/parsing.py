import sys
from heapq import heappush, heappop

from parsy import string, regex, seq

from models import SR, LR, NT, T


TOKEN = regex(r"\S+").map(str) # non-terminal, terminal or probability
ARROW = string("->")

SR_PARSER = seq( # syntactic rule parser (grammar.rules)
    TOKEN.skip(regex(r"\s+")),
    ARROW.skip(regex(r"\s+")),
    TOKEN.sep_by(regex(r"\s+"), min=2)
).map(lambda t: SR(
    label=NT(t[0]),
    child_labels=[NT(tok) for tok in t[2][:-1]],
    weight=float(t[2][-1])
))

LR_PARSER = seq( # lexical rule parser (grammar.lexicon)
    TOKEN.skip(regex(r"\s+")),   
    TOKEN.skip(regex(r"\s+")),       
    TOKEN                           
).map(lambda t: LR(
    label=NT(t[0]),
    word=T(t[1]),
    weight=float(t[2])
))


def load_binarized_syntactic_rules(path: str) -> list[SR]:
    """
    Loads syntactic rules from a grammar.rules file (assume already binarized)
    """
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
    """
    Load lexical rules from a grammar.lexicon file
    """
    rules: list[LR] = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rule = LR_PARSER.parse(line)
            rules.append(rule)
    return rules


def preprocess_rules(lexical_rules: str, syntactic_rules: str) -> tuple[dict[NT, int], list[tuple], list[list[int]]]:
    """
    Computes non-terminal encoding, indexed syntactic rules and the rule indices containing the particular non-terminals

    Notation: 
    - NT index: k
    - rule index: r
    """
    # encode non-terminals as integers
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
    # encode syntactic-rules using the encoded non-terminals
    indexed_syntactic_rules: list[tuple] = []
    for sr in syntactic_rules:
        indexed_syntactic_rules.append((
            sr.weight, 
            nt_idx[sr.label], 
            [nt_idx[cl] for cl in sr.child_labels]
        ))
    # determine the rules for each non-terminal where it is contained as a child
    contained: list[list[int]] = [[] for _ in range(len(nt_idx))]
    for r, isr in enumerate(indexed_syntactic_rules):
        for k in isr[2]: # isr[2] == syntactic rule children as encoded non-terminals
            contained[k].append(r)
    #
    return nt_idx, indexed_syntactic_rules, contained


def deduce(
        words: list[str], 
        lexical_rules: list[LR], 
        syntactic_rules: list[SR], 
        nt_idx: dict[NT, int], 
        indexed_syntactic_rules: list[tuple], 
        contained: list[list[int]],
        start
    ) -> str:
    """
    Deductive parsing algorithm producing a derivation tree in PTB format for the given sentense

    Args:
        words: sentence 
        lexical_rules: lexical rules
        syntactic_rules: syntactic rules.
        nt_idx: non-terminal encoding
        index_syntactic_rules: syntactic rules with encoded non-terminals,
        contained: rule indices where a particular non-terminal is contained
        start: root non-terminal

    Notation: 
    - word indices: i, j
    - NT index: k
    - rule index: r
    """
    # length constants
    N = len(words)
    M = len(syntactic_rules)
    # max probability function for a range [i, j) and a non-terminal A
    c: list[list[dict[int, float]]] = [[{} for _ in range(N+1)] for _ in range(N+1)]  # saves probability in c[i][j][A]
    # saves rule index and range split position in backtrace[i][j][A]
    backtrace: list[list[dict[int, tuple[int, int, int]]]] = [[{} for _ in range(N+1)] for _ in range(N+1)] 
    # precompute words set and word_positions
    word_set = set(words)
    word_positions: dict[str, list[int]] = {}
    for i, w in enumerate(words):
        if w not in word_positions:
            word_positions[w] = []
        word_positions[w].append(i)
    # initialize the priority queue with lexical rules
    priority_queue = [] # consists of (-weight, i, j, k, r, ij): negative weight trick to reverse the priority order; ij is a range split position
    covered = [False] * N 
    for r, lr in enumerate(lexical_rules):
        k = nt_idx[lr.label]
        if lr.word in word_set: 
            for i in word_positions[lr.word]:
                covered[i] = True
                heappush(priority_queue, (-lr.weight, i, i + 1, k, M + r, i + 1)) # ; lexical rules are indexed starting from M
    if not all(covered): # check whether all word positions are covered (if not => unknown token)
        return f"(NOPARSE {' '.join(words)})"
    # main parsing procedure for bottom-up deduction by matching syntactic rules
    while priority_queue:
        inv_w, i, j, k, r, ij = heappop(priority_queue)
        w = -inv_w
        if k not in c[i][j] or w > c[i][j][k]: # check if it is the best probability=weight for the range [i, j) and non-terminal indexed by k
            c[i][j][k] = w
            backtrace[i][j][k] = (r, ij)
            # apply the rules containing the non-terminal indexed by k
            for rr in contained[k]:
                ww, kk, children = indexed_syntactic_rules[rr] # k in children
                if len(children) == 1: # chain rule
                    heappush(priority_queue, (ww*inv_w, i, j, kk, rr, j)) # range splitting position is escaped as the right bound j
                else: # len(children) == 2
                    if children[0] == k: # left child
                        for jj in range(j + 1, N + 1): # check all possible positions for right bound extension
                            if children[1] in c[j][jj]:
                                heappush(priority_queue, (-1 * ww * w * c[j][jj][children[1]], i, jj, kk, rr, j))
                    if children[1] == k: # right child
                        for ii in range(0, i): # check all possible positions for left bound extension
                            if children[0] in c[ii][i]:
                                heappush(priority_queue, (-1 * ww * c[ii][i][children[0]] * w, ii, j, kk, rr, i))
    # sentence not parsable if the range [0, N) does not contain the root non-terming
    if nt_idx[start] not in c[0][N]:
        return f"(NOPARSE {' '.join(words)})"
    # build the derivation tree in PTB format from backtraces (top-down rule expansion)
    r, ij = backtrace[0][N][nt_idx[start]]
    stack = [(r, 0, ij, N)] # consists of (r, i, ij, j): left-side ranges at the top
    close_stack = [] # consists of indices where the right paranthesis has to be closed: left-side index at the top
    ptb = ""
    while stack:
        r, i, ij, j = stack.pop()
        # apply lexical rule
        if r >= M: 
            lr = lexical_rules[r - M]
            ptb += f"({lr.label} {lr.word})"
            while close_stack and close_stack[-1] == j: # if the lexical rule is the last subtree leaf => close the subtree structure
                _ = close_stack.pop()
                ptb += ")"
            ptb += " "
            continue
        # apply syntactic rule
        sr = syntactic_rules[r]
        ptb += f"({sr.label} "
        close_stack.append(j)
        if ij != j:  # not chain rule
            r2, ij2 = backtrace[ij][j][nt_idx[sr.child_labels[1]]]
            stack.append((r2, ij, ij2, j)) # append right-side range before the left-side range
        r1, ij1 = backtrace[i][ij][nt_idx[sr.child_labels[0]]]
        stack.append((r1, i, ij1, ij)) 
    return ptb.rstrip()

def parse_sentences(syntactic_rules_path: str, lexical_rules_path: str, start_symbol: str, unking: bool):
    """
    Parses the sentences one by one using syntactic and lexical rules
    """
    # load grammar rules and binarize if necessary
    lexical_rules = load_lexical_rules(path=lexical_rules_path)
    syntactic_rules  = load_binarized_syntactic_rules(path=syntactic_rules_path)
    # preprocess the rules once before parsing 
    nt_idx, indexed_syntactic_rules, contained = preprocess_rules(lexical_rules=lexical_rules, syntactic_rules=syntactic_rules)
    # read and parse the sentences one by one
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        words: list[str] = line.strip().split()
        # output the result of the deductive parsing algorithm
        print(deduce(
            words=words, 
            lexical_rules=lexical_rules,
            syntactic_rules=syntactic_rules,
            nt_idx=nt_idx,
            indexed_syntactic_rules=indexed_syntactic_rules,
            contained=contained,
            start=start_symbol
        ))