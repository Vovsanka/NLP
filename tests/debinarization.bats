setup() {
    set +e
    "$PROG" debinarise </dev/null
    [ "$?" -eq 22 ] && skip "status 22 => not implemented"
    set -e
}

@test "cli" {
    "$PROG" debinarise < "$DATA/bin.mrg" > debin.mrg
}

@test "output format" {
    diff <(sort debin.mrg | tr -s "\t" " ") <(sort "$DATA/debin.mrg")
}
