import sys

EXIT_NOT_IMPLEMENTED = 22

def not_implemented():
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
    # Placeholder: not implemented yet
    not_implemented()

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(EXIT_NOT_IMPLEMENTED)

    cmd = sys.argv[1]

    if cmd == "induce":
        cmd_induce(sys.argv[2:])
        return

    # Unknown command
    print(f"Unknown command: {cmd}")
    print_help()
    sys.exit(EXIT_NOT_IMPLEMENTED)

if __name__ == "__main__":
    main()
