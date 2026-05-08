import sys

from parsy import string, regex, seq, forward_declaration

from models import SE, T, NT, SR, LR


WS = regex(r"\s*") # optional whitespace
LPAR = string("(") # left paranthesis
RPAR = string(")") # right paranthesis
TOKEN = regex(r"[^()\s]+") # Terminal or Non-Terminal 

SE_PARSER = forward_declaration()

def build_symbolic_expression(parsed) -> SE:
    label, children = parsed
    return SE(NT(label), children)

SE_INNER = seq(
    TOKEN,  
    (WS >> (SE_PARSER | TOKEN)).many() 
).map(build_symbolic_expression)

SE_PARSER.become(LPAR >> WS >> SE_INNER << WS << RPAR)

def parse_ptb(tree: str) -> SE:
    parsed, rest = SE_PARSER.parse_partial(tree)

    if rest.strip():
        raise Exception(f"Extra content after first tree: {rest!r}")

    return parsed

def induce_grammar(grammar_prefix: str|None = None):
    # rule accumulation
    label_counter: dict[NT, int] = {}
    sr_counter: dict[SR, int] = {}  
    lr_counter: dict[LR, int] = {}
    words: set[T] = set()

    def accumulate_rules_and_words(se: SE):
        # accumulate the rule label
        if se.label not in label_counter:
            label_counter[se.label] = 0
        label_counter[se.label] += 1

        # lexical rule (NT -> T)
        if len(se.children) == 1 and isinstance(se.children[0], T):
            word = se.children[0]
            words.add(word)

            wr = LR(label=se.label, word=word)
            if wr not in lr_counter:
                lr_counter[wr] = 0
            lr_counter[wr] += 1

            return

        # the children are exclusively SE
        # syntactic rule (NT -> NT NT NT ...) 
        rule = SR(
            label=se.label,
            child_labels=[c.label for c in se.children]
        )
        if rule not in sr_counter:
            sr_counter[rule] = 0
        sr_counter[rule] += 1

        # recurse only into SE children
        for c in se.children:
            if isinstance(c, SE):
                accumulate_rules_and_words(c)

    # request the treebank input
    print("\nTraining Treebank: (one tree per line)")

    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        se: SE = parse_ptb(tree=line)
        # assert str(se) == line
        # accumulate rules and words
        accumulate_rules_and_words(se)

    # open the output files or use stdout
    if grammar_prefix is None:
        rules_f = sys.stdout
        lexicon_f   = sys.stdout
        words_f = sys.stdout
    else:
        rules_f = open(grammar_prefix + ".rules", "w")
        lexicon_f   = open(grammar_prefix + ".lexicon", "w")
        words_f = open(grammar_prefix + ".words", "w")
    
    # output the resulting PCFG (normalized) to stdout or to specified files
    # syntactic rules
    if grammar_prefix is None:
        print("\nGrammar.rules:")
    for rule, count in sr_counter.items():
        rule_str = f"{rule.label} -> "
        for cl in rule.child_labels:
            rule_str += f"{cl} "

        # add the rule probability
        prob = count/label_counter[rule.label]
        rule_str += str(int(prob)) if prob.is_integer() else str(prob)

        # write the syntactic rule
        rules_f.write(rule_str + "\n")

    # lexical rules
    if grammar_prefix is None:
        print("\nGrammar.lexicon:")
    for rule, count in lr_counter.items():
        rule_str = f"{rule.label} {rule.word} "

        # add the rule probability
        prob = count/label_counter[rule.label]
        if prob.is_integer(): 
            prob = int(prob) # adjust the formatting
        rule_str += str(prob)

        # write the syntactic rule
        lexicon_f.write(rule_str + "\n")
    
    # words
    if grammar_prefix is None:
        print("\nGrammar.words:")
    for w in sorted(words):
        words_f.write(w + "\n")
    
    # flush stdout or close the output files
    if grammar_prefix is not None:
        rules_f.close()
        lexicon_f.close()
        words_f.close()
    else:
        sys.stdout.flush()


        