def build_vertical_format(transactions):
    """Return dict: itemset (as frozenset) -> TID set."""
    vert = {}
    for tid, t in enumerate(transactions):
        for it in set(t):
            vert.setdefault(frozenset([it]), set()).add(tid)
    return vert

def eclat_recursive(prefix, items_tidsets, min_support, n_tx, out):
    while items_tidsets:
        (item, tidset) = items_tidsets.pop()
        new_prefix = prefix | item
        support = len(tidset) / n_tx if n_tx else 0
        if support >= min_support:
            out[new_prefix] = support
            # intersect with remaining to build extensions
            new_items = []
            for (item2, tidset2) in items_tidsets:
                inter = tidset & tidset2
                if inter:
                    new_items.append((item2, inter))
            eclat_recursive(new_prefix, new_items, min_support, n_tx, out)

def eclat(transactions, min_support=0.2):
    """
    Eclat algorithm in vertical format.
    Returns dict: {k: {frozenset(items): support}}
    """
    vert = build_vertical_format(transactions)
    items = list(vert.items())
    out = {}
    eclat_recursive(frozenset(), items, min_support, len(transactions), out)
    # group by k
    by_k = {}
    for iset, sup in out.items():
        by_k.setdefault(len(iset), {})[iset] = sup
    return by_k
