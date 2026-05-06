from typing import Union, List

T = Terminal = str # terminal = word
NT = NonTerminal = str # non-terminal = non-leaf tree node label
A = Atom = T | NT  # atom = token = terminal or non-terminal

class SymbolicExpression:
    # label: NT 
    # children: List[Union[Terminal, "SymbolicExpression"]] # [T] or [SE, SE, SE, ...]

    def __init__(self, label: NonTerminal, children: List[Union[Terminal, "SymbolicExpression"]]):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: symbolic expression must start with a non-terminal!")
        if not children:
            raise Exception("Parsing error: symbolic expression contains only one element!")

        self.label = label
        self.children = children

SE = SymbolicExpression # symbolic expression = non-leaf tree node