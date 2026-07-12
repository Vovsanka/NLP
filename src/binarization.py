import sys

from induction import parse_ptb

from models import SE, T, NT


def debinarise_trees():
    # print("\nBinarised Treebank: (one tree per line)")
    out = sys.stdout
    #
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        se: SE = parse_ptb(tree=line)
        # assert str(se) == line
        out.write(str(debinarise_one_tree(se)) + "\n")
    out.flush()


def binarise_trees(H: int, V: int):
    # print("\nTreebank: (one tree per line)")
    out = sys.stdout
    #
    for line in sys.stdin:
        # read the line with the tree from stdin
        line = line.rstrip("\n")
        if not line.strip():
            break  # finish if reached an empty line (or enter pressed)
        se: SE = parse_ptb(tree=line)
        # assert str(se) == line
        out.write(str(binarise_one_tree(se, H, V)) + "\n")
    out.flush()


def debinarise_one_tree(se: SE) -> SE:
    # remove the parent annotation
    original_label = se.label.split("^<", 1)[0]
    # preterminal (NT -> T)
    if len(se.children) == 1 and isinstance(se.children[0], T):
        return SE(
            label=original_label,
            children=se.children
        )
    # 1-2 children (NT -> NT) or (NT -> NT NT) (no more, because binarised!)
    direct_children: list[SE] = []
    current_se = se
    while True:
        direct_children.append(current_se.children[0])
        if len(current_se.children) == 1:
            break
        last_child = current_se.children[1]
        if "|<" in last_child.label:
            current_se = last_child
        else:
            direct_children.append(last_child)
            break
    #
    return SE(
        label=original_label,
        children=[debinarise_one_tree(se=child) for child in direct_children]
    )


def binarise_one_tree(se: SE, H: int, V: int, ancestors: list[NT] = [], original_se: SE | None = None):
    if original_se is None:
        original_se = se
    # preterminal (NT -> T)
    if len(se.children) == 1 and isinstance(se.children[0], T):
        return se
    # the children are exclusively SE
    add_parents_label = se.label
    if V > 1 and ancestors:
        add_parents_label += "^<"
        for anc in ancestors:
            add_parents_label += f"{anc},"
        add_parents_label = add_parents_label[:-1] + ">"
    #
    if V > 1: 
        new_ancestors = [original_se.label] + ancestors
        if len(new_ancestors) >= V:
            new_ancestors = new_ancestors[:-1]
    else:
        new_ancestors = []
    # 1-2 children (NT -> NT) or (NT -> NT NT)
    if len(se.children) <= 2:
        return SE(
            label=add_parents_label,
            children=[
                binarise_one_tree(se=child, H=H, V=V, ancestors=new_ancestors) for child in se.children
            ]
        )
    # 3+ children (NT -> NT NT NT ...) 
    new_node_label = original_se.label + "|<"
    for child in se.children[1:(H+1)]:
        new_node_label += child.label + ","
    new_node_label = new_node_label[:-1] + ">"
    return SE(
        label=add_parents_label,
        children=[
            binarise_one_tree(se=se.children[0], H=H, V=V, ancestors=new_ancestors),
            binarise_one_tree(
                se=SE(
                    label=new_node_label,
                    children=se.children[1:]
                ),
                H=H, V=V, 
                ancestors=ancestors, #Note: not new_ancestors!
                original_se=se
            )
        ],
    )




