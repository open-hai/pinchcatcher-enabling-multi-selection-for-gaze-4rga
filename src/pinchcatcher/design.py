"""Experimental design and counterbalancing (Sec. 4.1.2).

Stated: 5 techniques x 3 target numbers, 15 repetitions -> 225 trials per
participant; 2 training trials before each block with 10 spheres; block order
counterbalanced with a "Balanced Latin square"; 30 participants (Sec. 4.4).

Not stated: which balanced square. With an odd number of conditions (5) a
Williams square that balances first-order carry-over needs 2n = 10 sequences,
not 5. 30 participants divides evenly by both 5 and 10, so the participant
count does not disambiguate it. See params.LATIN_SQUARE_FORM.
"""

from typing import List

from . import params as P


def williams_square(n: int) -> List[List[int]]:
    """Williams design: n sequences if n is even, 2n if n is odd."""
    base = []
    for i in range(n):
        row = []
        for j in range(n):
            if j % 2 == 0:
                row.append((i + j // 2) % n)
            else:
                row.append((i - (j + 1) // 2) % n)
        base.append(row)
    if n % 2 == 1:
        base = base + [list(reversed(r)) for r in base]
    return base


def cyclic_latin_square(n: int) -> List[List[int]]:
    """The plain cyclic square some papers also call 'balanced'."""
    return [[(i + j) % n for j in range(n)] for i in range(n)]


def block_orders(n_participants=P.N_PARTICIPANTS, techniques=P.TECHNIQUES,
                 form=P.LATIN_SQUARE_FORM) -> List[List[str]]:
    n = len(techniques)
    square = williams_square(n) if form.startswith("williams") else cyclic_latin_square(n)
    return [[techniques[k] for k in square[p % len(square)]] for p in range(n_participants)]


def trial_schedule(participant: int, orders=None, repetitions=P.REPETITIONS,
                   target_counts=P.TARGET_COUNTS):
    """Ordered (block_index, technique, target_number, repetition) tuples."""
    orders = orders or block_orders()
    order = orders[participant]
    out = []
    for b, tech in enumerate(order):
        for rep in range(repetitions):
            for n_t in target_counts:
                out.append((b, tech, n_t, rep))
    return out


def design_report():
    orders = block_orders()
    n = len(P.TECHNIQUES)
    w = williams_square(n)
    # carry-over balance: does every ordered pair (a then b) appear equally often?
    pairs = {}
    for row in w:
        for a, b in zip(row, row[1:]):
            pairs[(a, b)] = pairs.get((a, b), 0) + 1
    counts = sorted(set(pairs.values()))
    return {
        "n_techniques": n,
        "williams_sequences": len(w),
        "cyclic_sequences": len(cyclic_latin_square(n)),
        "ordered_pairs_covered": len(pairs),
        "ordered_pairs_possible": n * (n - 1),
        "carryover_counts": counts,
        "carryover_balanced": len(counts) == 1 and len(pairs) == n * (n - 1),
        "participants": len(orders),
        "participants_per_sequence": len(orders) / len(w),
        "trials_per_participant": len(trial_schedule(0, orders)),
        "trials_stated_by_paper": P.TRIALS_TOTAL,
    }
