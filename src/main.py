import sys
import os

from induction import induce_grammar


EXIT_NOT_IMPLEMENTED = 22

def exit_not_implemented():
    sys.exit(EXIT_NOT_IMPLEMENTED)

def print_help():
    print("pcfg_tool [COMMAND]")
    print("Tools for PCFG-based parsing of natural language sentences.\n")
    print("Available commands:")
    print("  induce [GRAMMAR]   Induce a PCFG from constituent trees read from stdin.")
    print("                     If GRAMMAR is given, write GRAMMAR.rules,")
    print("                     GRAMMAR.lexicon, and GRAMMAR.words.")
    print()
    print("Run 'pcfg_tool COMMAND' to execute a specific function.")

def cmd_induce(args):
    print("Grammar Induction\n")
    print("Input: stdin (Treebank in Penn Treebank (PTB) format")

    if len(args) > 1:
        exit_not_implemented()
    
    grammar_prefix = args[0] if len(args) == 1 else None

    if grammar_prefix is None:
        print("Output: stdout with rules, lexicon, words (induced PCFG)")
    else:
        print(f"Output: {grammar_prefix}.rules, {grammar_prefix}.lexicon, {grammar_prefix}.words (induced PCFG)")

    induce_grammar(grammar_prefix=grammar_prefix)


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

    # Unknown command
    print(f"Unknown command: {cmd}")
    print_help()
    exit_not_implemented()
    


if __name__ == "__main__":
    main()
