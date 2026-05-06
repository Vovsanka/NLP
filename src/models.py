from typing import Union, List


class SymbolicExpression:
    # label: NonTerminal
    # children: List[Union[Terminal, "SymbolicExpression"]] # [T] or [SE, SE, SE, ...]

    def __init__(self, label: NonTerminal, children: List[Union[Terminal, "SymbolicExpression"]]):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: symbolic expression must start with a non-terminal!")
        if not children:
            raise Exception("Parsing error: symbolic expression contains only one element!")

        self.label = label
        self.children = children

class Rule:
    # label: NonTerminal
    # children: list[NonTerminal]

    def __init__(self, label: NonTerminal, children: list[NonTerminal]):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: rule label must be a non-terminal!")
        if not children:
            raise Exception("Parsing error: rule contains only one element!")

        self.label = label
        self.children = children


class Word:
    # label: NonTerminal
    # word: Terminal
    
    def __init__(self, label: NonTerminal, word: Terminal):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: token label must be a non-terminal!")
        if not isinstance(word, Terminal):
            raise Exception("Parsing error: token word must be a terminal!")

        self.label = label
        self.word = word


T = Terminal = str # terminal = word
NT = NonTerminal = str # non-terminal = non-leaf tree node label
A = Atom = T | NT  # atom = token = terminal or non-terminal
SE = SymbolicExpression # symbolic expression = non-leaf tree node
R = Rule # grammar rule
W = Word # word with its grammar label (different labels possible)



