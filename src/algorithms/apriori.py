import numpy as np
from itertools import combinations

def get_support(itemset, tx_list):
    """Compute support for a given itemset over a list of transactions (sets)."""
    count = 0
    s = set(itemset)
    for t in tx_list:
        if s.issubset(t):
            count += 1
    return count / len(tx_list) if tx_list else 0.0

def apriori(transactions, min_support=0.2):
    """
    Return dict: {k: {frozenset(items): support}} for each size k>=1.
    transactions: list of sets
    """
    item_counts = {}
    n_tx = len(transactions)
    for t in transactions:
        for it in set(t):
            item_counts[it] = item_counts.get(it, 0) + 1

    L = {}
    L1 = {frozenset([it]): c / n_tx
          for it, c in item_counts.items()
          if c / n_tx >= min_support}
    if not L1:
        return {}

    L[1] = L1
    k = 2
    current_L = L1

    while current_L:
        # generate candidates by self-join
        cand = set()
        keys = list(current_L.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                union = keys[i] | keys[j]
                if len(union) == k:
                    # prune: all (k-1)-subsets must be frequent
                    all_subfreq = all(
                        (union - frozenset([x])) in current_L
                        for x in union
                    )
                    if all_subfreq:
                        cand.add(union)

        # count support
        Ck = {}
        for c in cand:
            sup = get_support(c, transactions)
            if sup >= min_support:
                Ck[c] = sup

        if Ck:
            L[k] = Ck
            current_L = Ck
            k += 1
        else:
            break

    return L

def generate_rules(freq_dict, min_conf=0.5, n_tx=1):
    """
    Generate association rules (A -> B) with confidence >= min_conf.
    Returns a list of dicts with keys: antecedent, consequent, support, confidence, lift.
    """
    # build quick support lookup
    sup_lookup = {}
    for k, m in freq_dict.items():
        for iset, sup in m.items():
            sup_lookup[iset] = sup

    rules = []
    for k, m in freq_dict.items():
        if k < 2:
            continue
        for iset, sup_ab in m.items():
            items = list(iset)
            # all non-empty proper subsets as antecedents
            for r in range(1, len(items)):
                for A in combinations(items, r):
                    A = frozenset(A)
                    B = iset - A
                    sup_a = sup_lookup.get(A, 0)
                    sup_b = sup_lookup.get(B, 0)
                    if sup_a == 0 or len(B) == 0:
                        continue
                    conf = sup_ab / sup_a
                    if conf >= min_conf:
                        lift = conf / sup_b if sup_b > 0 else np.nan
                        rules.append({
                            'antecedent': tuple(sorted(A)),
                            'consequent': tuple(sorted(B)),
                            'support': sup_ab,
                            'confidence': conf,
                            'lift': lift
                        })

    # sort by confidence desc, then lift desc
    rules.sort(key=lambda x: (x['confidence'], x['lift']), reverse=True)
    return rules
