setup() {
    set +e
    "$PROG" binarise </dev/null
    [ "$?" -eq 22 ] && skip "status 22 => not implemented"
    set -e
}

@test "cli with h and v arguments" {
    "$PROG" binarise -h 999 -v 1 < "$DATA/debin.mrg"
}

@test "cli without h and v arguments" {
    "$PROG" binarise < "$DATA/debin.mrg" > bin.mrg
}

@test "output format" {
    diff <(sort bin.mrg | tr -s "\t" " ") <(sort "$DATA/bin.mrg")
}
