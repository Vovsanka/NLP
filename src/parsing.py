import sys

ESCAPE_TOKENS = {
    "(": "-LPAR-",
    ")": "-RPAR-",
    " ": "_"
}

def parse_sentences(syntactic_rules_path: str, lexical_rules_path: str):
    # load and binarize grammar rules 
    syntactic_rules  = load_binarized_syntactic_rules(syntactic_rules_path=syntactic_rules_path)
    lexical_rules = load_binarized_lexical_rules(lexical_rules_path=lexical_rules_path)
    # read and parse the sentences one by one
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        sentence = preprocess_raw_sentence(sentence=line)
        # TODO: implement a parsing algorithm (CYK or deductive? think of datastructures for the rules)