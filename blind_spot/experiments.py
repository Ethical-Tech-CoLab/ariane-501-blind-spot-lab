"""Seeded, synthetic tests. Probabilities here are not historical flight risks."""

from dataclasses import asdict, dataclass, replace
import random

from .coverage import coverage_experiment
from .model import Design, Stimulus, evaluate, latent_trigger, oracle_detects
from .statistics import (
    detection_probability, positive_count, tests_for_detection,
    wilson_interval, zero_failure_upper,
)


SEED = 5011996
MODEL_VERSION = "1.1"
REPORT_DIGITS = 12


def reported_probability(value: float) -> float:
    """Discard platform-libm last-bit noise only at the publication boundary."""
    return float(f"{value:.{REPORT_DIGITS}g}")


@dataclass(frozen=True)
class Experiment:
    name: str
    profile: str
    n: int
    seed: int
    expected_detection_p: float
    design: Design = Design()
    oracle: str = "safety"


def draw_stimulus(rng: random.Random, profile: str) -> Stimulus:
    if profile == "legacy":
        bh = rng.uniform(0.0, 30000.0)
    elif profile == "expanded":
        bh = rng.uniform(0.0, 65535.0)
    elif profile == "rare_tail":
        bh = rng.uniform(32768.0, 65535.0) if rng.random() < 0.001 else rng.uniform(0.0, 30000.0)
    else:
        raise ValueError(f"Unknown input profile: {profile}")
    return Stimulus(bh, rng.uniform(0.0, 80.0))


def run_experiment(spec: Experiment) -> dict:
    positive_count(spec.n)
    rng = random.Random(spec.seed)
    counts = {"latent_triggers": 0, "navigation_losses": 0, "unsafe_commands": 0, "detected": 0}
    for _ in range(spec.n):
        stimulus = draw_stimulus(rng, spec.profile)
        outcome = evaluate(stimulus, spec.design)
        counts["latent_triggers"] += latent_trigger(stimulus)
        counts["navigation_losses"] += not outcome.navigation_available
        counts["unsafe_commands"] += outcome.unsafe_command
        counts["detected"] += oracle_detects(outcome, spec.oracle)
    return {
        **asdict(spec), **counts,
        "detected_rate": counts["detected"] / spec.n,
        "wilson_95": [reported_probability(bound) for bound in wilson_interval(counts["detected"], spec.n)],
        "zero_failure_upper_95": reported_probability(zero_failure_upper(spec.n)) if counts["detected"] == 0 else None,
    }


def ablations() -> list[dict]:
    stimulus = Stimulus(40000.0, 20.0)
    baseline = Design()
    designs = {
        "baseline_identical_pair": baseline,
        "one_unit": replace(baseline, replicas=1),
        "three_identical_units": replace(baseline, replicas=3),
        "remove_postlaunch_alignment": replace(baseline, alignment_retained=False),
        "guard_alignment_conversion": replace(baseline, conversion_guard=True),
        "isolate_alignment_exception": replace(baseline, isolate_alignment_failure=True),
        "reject_diagnostic_frame": replace(baseline, diagnostic_guard=True),
        "idealized_sri_stub": replace(baseline, software_in_loop=False),
    }
    return [
        {"name": name, **asdict(evaluate(stimulus, design)),
         "detected": oracle_detects(evaluate(stimulus, design))}
        for name, design in designs.items()
    ]


def probability_table() -> list[dict]:
    return [
        {
            "p": p, "tests_for_95_percent": tests_for_detection(p),
            "detection_by_budget": {
                str(n): reported_probability(detection_probability(p, n))
                for n in (10, 100, 1000, 10000, 1000000)
            },
        }
        for p in (0.0, 0.000001, 0.0005, 0.01, 0.25)
    ]


def run_study() -> dict:
    baseline = Design()
    specs = [
        Experiment("million_legacy", "legacy", 1000000, SEED, 0.0),
        Experiment("expanded_faithful", "expanded", 100000, SEED + 1, 0.25),
        Experiment("rare_tail_faithful", "rare_tail", 200000, SEED + 2, 0.0005),
        Experiment("expanded_idealized_stub", "expanded", 100000, SEED + 1, 0.0,
                   replace(baseline, software_in_loop=False)),
        Experiment("expanded_packet_oracle", "expanded", 100000, SEED + 1, 0.0,
                   baseline, "packet"),
        Experiment("expanded_alignment_removed", "expanded", 100000, SEED + 1, 0.0,
                   replace(baseline, alignment_retained=False)),
    ]
    return {
        "model_version": MODEL_VERSION,
        "reported_probability_significant_digits": REPORT_DIGITS,
        "seed": SEED,
        "data_class": "synthetic; no flight telemetry",
        "independence": "iid test opportunities, not independent redundant software",
        "monte_carlo": [run_experiment(spec) for spec in specs],
        "probability_table": probability_table(),
        "ablations": ablations(),
        "coverage": coverage_experiment(),
    }
