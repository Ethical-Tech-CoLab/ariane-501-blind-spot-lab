"""Small exhaustive Boolean design and a constructive pairwise counterexample."""

from itertools import combinations, product

from .model import Design, Stimulus, evaluate, oracle_detects


FACTORS = (
    "high_bh", "early_time", "alignment_retained", "conversion_guard",
    "isolate_alignment_failure", "diagnostic_guard", "software_in_loop",
    "safety_oracle",
)
Row = tuple[bool, ...]
Interaction = tuple[tuple[int, bool], ...]


def all_rows() -> list[Row]:
    return list(product((False, True), repeat=len(FACTORS)))


def row_outcome(row: Row):
    if len(row) != len(FACTORS) or any(type(v) is not bool for v in row):
        raise ValueError("A design row must contain eight Boolean factors")
    high, early, retained, guarded, isolated, diag_guard, faithful, safety = row
    outcome = evaluate(
        Stimulus(40000.0 if high else 20000.0, 20.0 if early else 50.0),
        Design(retained, guarded, isolated, diag_guard, faithful),
    )
    return outcome, oracle_detects(outcome, "safety" if safety else "packet")


def interactions(row: Row, strength: int = 2) -> set[Interaction]:
    if not 1 <= strength <= len(FACTORS):
        raise ValueError("Interaction strength must be in [1, 8]")
    return {
        tuple((i, row[i]) for i in indices)
        for indices in combinations(range(len(FACTORS)), strength)
    }


def greedy_cover(candidates: list[Row], universe: set[Interaction]) -> list[Row]:
    remaining = set(universe)
    selected = []
    pool = [(row, interactions(row)) for row in candidates]
    while remaining:
        row, covered = max(pool, key=lambda entry: len(entry[1] & remaining))
        if not covered & remaining:
            raise ValueError("Candidates cannot cover the requested interaction universe")
        selected.append(row)
        remaining -= covered
    return selected


def coverage_experiment() -> dict:
    rows = all_rows()
    universe = set().union(*(interactions(row) for row in rows))
    # Deliberately construct a witness, NOT a claim about typical pairwise tools.
    safe_candidates = [row for row in rows if row_outcome(row)[0].navigation_available]
    suites = {
        "exhaustive": rows,
        "greedy_pairwise": greedy_cover(rows, universe),
        "pairwise_blind_witness": greedy_cover(safe_candidates, universe),
    }
    result = {"factors": list(FACTORS), "pair_universe": len(universe), "suites": {}}
    for name, suite in suites.items():
        covered = set().union(*(interactions(row) for row in suite))
        outcomes = [row_outcome(row) for row in suite]
        result["suites"][name] = {
            "cases": len(suite),
            "pairs_covered": len(covered),
            "pair_coverage": len(covered) / len(universe),
            "navigation_losses": sum(not outcome.navigation_available for outcome, _ in outcomes),
            "detected": sum(detected for _, detected in outcomes),
            "unsafe_commands": sum(outcome.unsafe_command for outcome, _ in outcomes),
            "rows": [list(row) for row in suite],
        }
    return result
