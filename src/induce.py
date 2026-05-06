import sys

from parsy import string, regex, seq, forward_declaration

from models import SE, T, NT, R, W

def parse_ptb():
    pass
    # TODO: implement

def induce_grammar(grammar_prefix: str|None = None):
    # rule accumulation
    rule_counter: dict[R, int] = {}  
    word_counter: dict[W, int] = {}
    words: set[T] = {}
    # request the treebank input
    print("\nTraining Treebank: (one tree per line)")
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            continue  # skip empty lines
        se: SE = parse_ptb(line)
        # TODO: accumulate
    
    #TODO: normalize and create grammer (save to 3 files or write to stdout)
    print("\n")
        
    