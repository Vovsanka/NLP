import sys

from parsy import string, regex, seq, forward_declaration

from models import SE, T, NT

def parsePTB():
    pass
    # TODO: implement

def induce_grammar(grammar_prefix: str|None = None):
    # rule accumulation
    # TODO: rules counter (map),  lexicon counter (map), word terminals (set) 
    # request the treebank input
    print("\nTraining Treebank: (one tree per line)")
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            continue  # skip empty lines
        se: SE = parsePTB(line)
        # TODO: accumulate
    
    #TODO: normalize and create grammer (save to 3 files or write to stdout)
    print("\n")
        
    