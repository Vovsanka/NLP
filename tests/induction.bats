setup() {
    set +e
    "$PROG" induce </dev/null
    [ "$?" -eq 22 ] && skip "status 22 => not implemented"
    set -e
}

@test "cli without grammar name" {
    "$PROG" induce < "$DATA/training.mrg"
}

@test "cli with grammar name" {
    "$PROG" induce $TESTRUN/cli < "$DATA/training.mrg"
}

@test "output format" {
    for FILE in cli.{rules,lexicon,words}; do
        [ -f "$TESTRUN/$FILE" ]
        diff <(sort < "$FILE" | tr -s "\t" " ") <(sort < "$DATA/$FILE" | tr -s "\t" " ")
    done
}
