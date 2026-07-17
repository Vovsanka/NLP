import sys

from induction import parse_ptb

from models import SE, T, NT


def unk_trees(threshold: int, smoothing: bool = False):
    # count the entries of each word (absolute frequency)
    word_counter: dict[T, int] = {}
    # accumlate the word count 
    def accumulate_words(se: SE):
        # preterminal (NT -> T)
        if len(se.children) == 1 and isinstance(se.children[0], T):
            word = se.children[0]
            if word not in word_counter:
                word_counter[word] = 0
            word_counter[word] += 1
            return
        # the children are exclusively SE
        for child in se.children:
            accumulate_words(se=child)
    # read the trees line by line and count the word entries
    # print("\nTreebank: (one tree per line)")
    syntactic_expressions: list[SE] = []
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        se: SE = parse_ptb(tree=line)
        # assert str(se) == line
        accumulate_words(se)
        syntactic_expressions.append(se)
    # replace rare words with UNK or signature (for smoothing)    
    leaf = 0 # leaf number is indexed from 1
    def replace_rare_words_with_unk(se: SE) -> SE:
        nonlocal leaf
        # preterminal (NT -> T)
        if len(se.children) == 1 and isinstance(se.children[0], T):
            leaf += 1
            word = se.children[0]
            if word not in word_counter or word_counter[word] <= threshold:
                return SE(
                    label=se.label,
                    children=[get_unknown_signature(word=word, i=leaf, smoothing=smoothing)]
                )
            else:
                return se
        # the children are exclusively SE
        return SE(
            label=se.label,
            children=[replace_rare_words_with_unk(child) for child in se.children]
        )
    # output the modified tree to stdout
    out = sys.stdout
    for se in syntactic_expressions:
        out.write(str(replace_rare_words_with_unk(se)) + "\n")
    out.flush()


def get_unknown_signature(word: T, i: int, smoothing: bool) -> T:  # i = word index starting from 1
    unk_sign = "UNK"
    # The signature is just UNK if no smoothing is applied
    if not smoothing or len(word) == 0:
        return T(unk_sign)
    # Letter suffix 
    if word[0].isupper() and not any(c.islower() for c in word):
        unk_sign += "-AC"
    elif word[0].isupper() and i == 1:
        unk_sign += "-SC"
    elif word[0].isupper():
        unk_sign += "-C"
    elif any(c.islower() for c in word):
        unk_sign += "-L"
    elif any(c.isalpha() for c in word):
        unk_sign += "-U"
    else:
        unk_sign += "-S"
    # Number suffix
    if all(c.isdigit() for c in word):
        unk_sign += "-N"
    elif any(c.isdigit() for c in word):
        unk_sign += "-n"
    # Dash suffix
    if "-" in word:
        unk_sign += "-H"
    # Period suffix
    if "." in word:
        unk_sign += "-P"
    # Comma suffix
    if "," in word:
        unk_sign += "-C"
    # Word suffix
    if len(word) > 3 and word[-1].isalpha():
        unk_sign += "-" + word[-1].lower()
    # The signature is a UNK with the suffixes
    return T(unk_sign)



