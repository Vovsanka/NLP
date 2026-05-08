setup() {
    set +e
    "$PROG" parse /dev/null /dev/null </dev/null
    [ "$?" -eq 22 ] && skip "status 22 => not implemented"
    set -e
}

function no_stderr {
    "$@" 2>/dev/null
}

@test "cli with default initial nonterminal" {
    "$PROG" parse "$DATA"/test.{rules,lexicon} < "$DATA/sentences" > parsed.mrg
}

@test "output format" {
    diff <(sort parsed.mrg | tr -s "\t" " ") <(sort "$DATA/parsed.mrg")
}

@test "cli with initial nonterminal" {
    run no_stderr "$PROG" parse -i WURZEL "$DATA"/parsing-testcli.{rules,lexicon} < <(echo "a a b b b")
    [ "$status" -eq 0 ]
    [ "$output" = "(WURZEL (X (A a) (X a)) (Y (B b) (Y (B b) (Y b))))" ]
}
