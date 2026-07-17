import sys
from sortedcontainers import SortedList

from parsy import string, regex, seq

from models import SR, LR, NT, T

from unking import get_unknown_signature


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


def load_syntactic_rules(path: str) -> list[SR]:
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

def load_indexed_outside(path: str, nt_idx: dict[NT, int]) -> list[float]:
    indexed_outside: list[float] = [0] * len(nt_idx)
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            [nonterminal, out_weight] = line.split()
            indexed_outside[nt_idx[nonterminal]] = float(out_weight)
    return indexed_outside


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
        start: NT,
        beam_threshold: float,
        beam_rank: int,
        out: list[float]
    ) -> str | None:
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
    priority_queue = SortedList() # consists of (weight, i, j, k, r, ij)
    def priority_queue_pop_best():
        return priority_queue.pop(-1) # return the element with the largest weight
    def priority_queue_pop_worst():
        return priority_queue.pop(0)
    def get_max_weight():
        return priority_queue[-1][0]
    def get_min_weight():
        return priority_queue[0][0]
    # check whether all word positions are covered
    covered = [False] * N 
    for r, lr in enumerate(lexical_rules):
        k = nt_idx[lr.label]
        if lr.word in word_set: 
            for i in word_positions[lr.word]:
                covered[i] = True
                priority_queue.add((lr.weight, i, i + 1, k, M + r, i + 1)) # lexical rules are indexed starting from M
    if not all(covered):
        return None
    # prune the priority queue by threshold or size
    def prune():
        if not priority_queue:
            return
        best_w = get_max_weight()
        m = beam_threshold * best_w 
        while priority_queue and get_min_weight() <= m: 
            priority_queue_pop_worst()
        if len(priority_queue) > beam_rank:
            del priority_queue[:-beam_rank]
    # main parsing procedure for bottom-up deduction by matching syntactic rules
    while priority_queue:
        w, i, j, k, r, ij = priority_queue_pop_best()
        if k in out:
            w *= out[k]
        if k not in c[i][j] or w > c[i][j][k]: # check if it is the best probability=weight for the range [i, j) and non-terminal indexed by k
            c[i][j][k] = w
            backtrace[i][j][k] = (r, ij)
            # apply the rules containing the non-terminal indexed by k
            for rr in contained[k]:
                ww, kk, children = indexed_syntactic_rules[rr] # k in children
                if len(children) == 1: # chain rule
                    priority_queue.add((ww * w, i, j, kk, rr, j)) # range splitting position is escaped as the right bound j
                else: # len(children) == 2
                    if children[0] == k: # left child
                        for jj in range(j + 1, N + 1): # check all possible positions for right bound extension
                            if children[1] in c[j][jj]:
                                priority_queue.add((ww * w * c[j][jj][children[1]], i, jj, kk, rr, j))
                    if children[1] == k: # right child
                        for ii in range(0, i): # check all possible positions for left bound extension
                            if children[0] in c[ii][i]:
                                priority_queue.add((ww * c[ii][i][children[0]] * w, ii, j, kk, rr, i))
            prune()
    # sentence not parsable if the range [0, N) does not contain the root non-terming
    if nt_idx[start] not in c[0][N]:
        return None
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

def parse_sentences(
        syntactic_rules_path: str, 
        lexical_rules_path: str, 
        start_symbol: str, 
        unking: bool, 
        smoothing: bool,
        beam_threshold: float,
        beam_rank: int,
        astar_path: str  
    ):
    """
    Parses the sentences one by one using syntactic and lexical rules
    """
    # load grammar rules and determine the words
    lexical_rules: list[LR] = load_lexical_rules(path=lexical_rules_path)
    syntactic_rules: list[SR]  = load_syntactic_rules(path=syntactic_rules_path)
    #
    vocabulary: set[T] = set([lr.word for lr in lexical_rules])
    # preprocess the rules once before parsing 
    nt_idx, indexed_syntactic_rules, contained = preprocess_rules(lexical_rules=lexical_rules, syntactic_rules=syntactic_rules)
    # read and parse the sentences one by one
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        words: list[T] = [T(w) for w in line.strip().split()]
        # replace unknown words by UNK
        original_words: list[T] | None = None
        if unking or smoothing:
            original_words = words.copy()
            unked_word_positions: list[int] = []
            unked_word_signatures: list[T] = []
            for i, w in enumerate(original_words):
                if w not in vocabulary:
                    words[i] = get_unknown_signature(w, i, smoothing)
                    unked_word_positions.append(i)
                    unked_word_signatures.append(words[i])
        # output the result of the deductive parsing algorithm
        parsed_ptb = deduce(
            words=words, 
            lexical_rules=lexical_rules,
            syntactic_rules=syntactic_rules,
            nt_idx=nt_idx,
            indexed_syntactic_rules=indexed_syntactic_rules,
            contained=contained,
            start=start_symbol,
            beam_threshold=beam_threshold,
            beam_rank=beam_rank,
            out=load_indexed_outside(path=astar_path, nt_idx=nt_idx) if astar_path else {}
        )
        #
        out = sys.stdout
        # output the derivation tree or NOPARSE
        if unking or smoothing:
            if parsed_ptb is None:
                out.write(f"(NOPARSE {' '.join(original_words)})\n")
            else:
                # restore the original words in the derivation tree
                no_unking_ptb = ""
                current_unked_word_position_index = 0
                j = 0
                while j < len(parsed_ptb):
                    if current_unked_word_position_index < len(unked_word_positions) and \
                       parsed_ptb.startswith(f" {unked_word_signatures[current_unked_word_position_index]})", j):
                        # restore the original unknown word
                        unked_word = original_words[unked_word_positions[current_unked_word_position_index]]
                        no_unking_ptb += f" {unked_word}"
                        j += len(unked_word_signatures[current_unked_word_position_index]) + 1
                        # 
                        current_unked_word_position_index += 1
                    else:
                        # add the current symbol
                        no_unking_ptb += parsed_ptb[j]
                        j += 1
                out.write(no_unking_ptb + "\n")
        else:
            if parsed_ptb is None:
                out.write(f"(NOPARSE {' '.join(words)})\n")
            else:
                out.write(parsed_ptb + "\n")


