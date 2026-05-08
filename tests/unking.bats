setup() {
    set +e
    "$PROG" unk -t 1 </dev/null
    [ "$?" -eq 22 ] && skip "status 22 => not implemented"
    set -e
}

@test "cli" {
    "$PROG" unk -t 1 < "$DATA/training.mrg" > unked.mrg
}

@test "output format" {
    diff <(sort unked.mrg | tr -s "\t" " ") <(sort "$DATA/unked.mrg")
}

@test "no unking reflection, no parse" {
    output=$(head -n 1 "$DATA"/sentences | "$PROG" parse "$DATA"/unked.{rules,lexicon})
    diff <(echo "$output" | tr -s "\t" " ") <(echo "(NOPARSE a b)")
}

@test "unking reflection, parse successful" {
    output=$(head -n 1 "$DATA"/sentences | "$PROG" parse -u "$DATA"/unked.{rules,lexicon})
    diff <(echo "$output" | tr -s "\t" " ") <(head -n 1 "$DATA/parsed.mrg")
}
