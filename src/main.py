import sys
import os

from induction import induce_grammar
from parsing import parse_sentences
from binarization import binarise_trees, debinarise_trees


EXIT_NOT_IMPLEMENTED = 22

def exit_not_implemented():
    print("NOT IMPLEMENTED EXIT")
    sys.exit(EXIT_NOT_IMPLEMENTED)

def print_help():
    print("pcfg_tool [COMMAND]")
    print("Tools for PCFG-based parsing of natural language sentences.\n")
    print("Available commands:")
    print("  induce [GRAMMAR])")
    print("                     Induce a PCFG from constituent trees read from stdin.")
    print("                     If GRAMMAR is given, write GRAMMAR.rules,")
    print("                     GRAMMAR.lexicon, and GRAMMAR.words.")
    print()
    print("  parse [OPTIONS] RULES LEXICON")
    print("                     Parse sentences read from standard input using the")
    print("                     PCFG defined by RULES and LEXICON. Sentences must be")
    print("                     whitespace-separated tokens. For each sentence, output")
    print("                     the highest-probability parse tree or a NOPARSE tree.")
    print("         -i --initial-nonterminal =N")
    print("                     Define N as the start non -terminal.")
    print("                     Default: ROOT.")
    print()
    print("  binarise [OPTIONS]")
    print("                     Binarise a sequence of constituent trees read from stdin.")
    print("                     Output the corresponding binarized constituent trees to stdout.")
    print("         -h --horizontal =H")
    print("                     Horizontal markovization with H.")
    print("                     Default: infinite (999).")
    print("         -v --vertical=V")
    print("                     Vertical markovization with V.")
    print("                     Default: 1.")
    print()
    print("  debinarise")
    print("                     Debinarise a sequence of constituent trees read from stdin.")
    print("                     Output the corresponding binarized constituent trees to stdout.")
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
        if len(args) < 2:
            exit_not_implemented()
        if args[0] in ("-i", "--initial-nonterminal"):
            start_symbol = args[1]
        else:
            exit_not_implemented()
        args = args[2:]
        

    if len(args) != 2:
        exit_not_implemented()
    
    syntactic_rules_path = args[0]
    lexical_rules_path = args[1]

    parse_sentences(
        syntactic_rules_path=syntactic_rules_path,
        lexical_rules_path=lexical_rules_path,
        start_symbol=start_symbol  
    )

def cmd_binarise(args: list):
    H = 999
    V = 1
    while args and args[0].startswith("-"):
        if len(args) < 2:
            exit_not_implemented()
        if args[0] in ("-h", "--horizontal"):
            H = int(args[1])
        elif args[0] in ("-v", "--vertical"):
            V = int(args[1])
        else:
            exit_not_implemented()
        args = args[2:]

    if len(args) != 0:
        exit_not_implemented()

    binarise_trees(H=H, V=V)

def cmd_debinarise(args: list):
    if len(args) != 0:
        exit_not_implemented()
    debinarise_trees()


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
    
    if cmd == "binarise":
        cmd_binarise(sys.argv[2:])
        return 
    
    if cmd == "debinarise":
        cmd_debinarise(sys.argv[2:])
        return 

    # Unknown command
    print(f"Unknown command: {cmd}")
    print_help()
    exit_not_implemented()
    


if __name__ == "__main__":
    main()
