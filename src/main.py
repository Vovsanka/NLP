import sys
import os

from induction import induce_grammar
from parsing import parse_sentences


EXIT_NOT_IMPLEMENTED = 22

def exit_not_implemented():
    print("NOT IMPLEMENTED EXIT")
    sys.exit(EXIT_NOT_IMPLEMENTED)

def print_help():
    print("pcfg_tool [COMMAND]")
    print("Tools for PCFG-based parsing of natural language sentences.\n")
    print("Available commands:")
    print("  induce [GRAMMAR]   Induce a PCFG from constituent trees read from stdin.")
    print("                     If GRAMMAR is given, write GRAMMAR.rules,")
    print("                     GRAMMAR.lexicon, and GRAMMAR.words.")
    print()
    print("  parse [-i ROOT | --initial ROOT] RULES LEXICON")
    print("                     Parse sentences read from standard input using the")
    print("                     PCFG defined by RULES and LEXICON. Sentences must be")
    print("                     whitespace-separated tokens. For each sentence, output")
    print("                     the highest-probability parse tree or a NOPARSE tree.")
    print()
    print("Run 'pcfg_tool COMMAND' to execute a specific function.")


def cmd_induce(args: list):
    # print("Grammar Induction\n")
    # print("Input: stdin (Treebank in Penn Treebank [PTB] format)")

    if len(args) > 1:
        exit_not_implemented()
    
    grammar_prefix = args[0] if len(args) == 1 else None

    if grammar_prefix is None:
        print("Output: stdout with rules, lexicon, words (induced PCFG)")
    else:
        print(f"Output: {grammar_prefix}.rules, {grammar_prefix}.lexicon, {grammar_prefix}.words (induced PCFG)")

    induce_grammar(grammar_prefix=grammar_prefix)

def cmd_parse(args: list):
    # print("Sentence Parsing\n")
    # print("Input: grammar.rules grammar.lexicon < sentences")
    # print("Output: best parse tree (in Penn Treebank [PTB] format)")

    start_symbol = "ROOT"
    while args and args[0].startswith("-"):
        if args[0] in ("-i", "--initial"):
            if len(args) < 2:
                exit_not_implemented()
            start_symbol = args[1]
            args = args[2:]
        else:
            exit_not_implemented()

    if len(args) != 2:
        exit_not_implemented()
    
    syntactic_rules_path = args[0]
    lexical_rules_path = args[1]

    parse_sentences(
        syntactic_rules_path=syntactic_rules_path,
        lexical_rules_path=lexical_rules_path,
        start_symbol=start_symbol  
    )



def main():
    """
    CLI entry point
    """
    if len(sys.argv) < 2:
        print_help()
        exit_not_implemented()

    cmd = sys.argv[1]

    if cmd == "induce":
        cmd_induce(sys.argv[2:])
        return
    
    if cmd == "parse":
        cmd_parse(sys.argv[2:])
        return 

    # Unknown command
    print(f"Unknown command: {cmd}")
    print_help()
    exit_not_implemented()
    


if __name__ == "__main__":
    main()
