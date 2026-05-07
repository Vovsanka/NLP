from typing import Union, List


T = Terminal = str # terminal = word
NT = NonTerminal = str # non-terminal = non-leaf tree node label
A = Atom = T | NT  # atom = token = terminal or non-terminal


class SymbolicExpression:
    # label: NonTerminal
    # children: List[Union[Terminal, "SymbolicExpression"]] 

    def __init__(self, label: NonTerminal, children: List[Union[Terminal, "SymbolicExpression"]]):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: symbolic expression must start with a non-terminal!")
        if not children:
            raise Exception("Parsing error: symbolic expression contains only one element!")
        if not(len(children) == 1 and isinstance(children[0], Terminal)):
            for c in children:
                if isinstance(c, Terminal):
                    raise Exception("Parsing error: symbolic expression children must be either a single terminal or a non-empty list of non-terminals!")


        self.label = label
        self.children = children

    def __str__(self) -> str:
        child_strs = []
        for c in self.children:
            if isinstance(c, SymbolicExpression):
                child_strs.append(str(c))
            else:
                child_strs.append(c)
        return f"({self.label} {' '.join(child_strs)})"

    def __repr__(self) -> str:
        return str(self)


class SyntacticRule:
    # label: NonTerminal
    # children: list[NonTerminal]

    def __init__(self, label: NonTerminal, child_labels: list[NonTerminal]):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: rule label must be a non-terminal!")
        if not child_labels:
            raise Exception("Parsing error: rule contains only one element!")

        self.label = label
        self.child_labels = child_labels

    def __eq__(self, other):
        return (
            isinstance(other, SyntacticRule)
            and self.label == other.label
            and self.child_labels == other.child_labels
        )

    def __hash__(self):
        return hash((self.label, tuple(self.child_labels)))



class LexicalRule:
    # label: NonTerminal
    # word: Terminal
    
    def __init__(self, label: NonTerminal, word: Terminal):
        if not isinstance(label, NonTerminal):
            raise Exception("Parsing error: token label must be a non-terminal!")
        if not isinstance(word, Terminal):
            raise Exception("Parsing error: token word must be a terminal!")

        self.label = label
        self.word = word

    def __eq__(self, other):
        return (
            isinstance(other, LexicalRule)
            and self.label == other.label
            and self.word == other.word
        )

    def __hash__(self):
        return hash((self.label, self.word))



SE = SymbolicExpression # symbolic expression = non-leaf tree node
SR = SyntacticRule # grammar rule 
LR = LexicalRule # grammar rule with a terminal



