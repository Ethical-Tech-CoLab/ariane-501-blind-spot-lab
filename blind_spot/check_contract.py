"""A release-style evaluation: the known-bad design must fail the contract."""

import argparse

from .model import Design, Stimulus, evaluate, oracle_detects


CASES = (
    ("representable_before_cutoff", Stimulus(32767.0, 20.0)),
    ("positive_overflow_before_cutoff", Stimulus(40000.0, 20.0)),
    ("negative_overflow_before_cutoff", Stimulus(-40000.0, 20.0)),
    ("out_of_range_after_cutoff", Stimulus(40000.0, 50.0)),
)


def contract_violations(design: Design) -> list[str]:
    return [name for name, stimulus in CASES if oracle_detects(evaluate(stimulus, design))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", choices=("baseline", "alignment-removed"), default="baseline")
    args = parser.parse_args()
    design = Design(alignment_retained=args.design == "baseline")
    violations = contract_violations(design)
    for name in violations:
        print(f"FAIL {name}: required navigation/command contract violated")
    print(f"{len(CASES) - len(violations)}/{len(CASES)} contract cases passed ({args.design}).")
    raise SystemExit(1 if violations else 0)


if __name__ == "__main__":
    main()
