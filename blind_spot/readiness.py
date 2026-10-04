"""Controlled prerequisite removals, not a blind discovery or human-response trial."""

from dataclasses import asdict, replace
from itertools import product

from .model import Design, Stimulus, evaluate, oracle_detects
from .statistics import detection_probability, tests_for_detection


FACTORS = (
    "overflow_support", "alignment_reachable", "implementation_in_loop",
    "safety_oracle", "adequate_budget", "retain_replay", "enforce_response",
)
BASE_DETECTION_P = 0.001 * 0.5
TARGET = 0.95
SHORT_BUDGET = 10
TARGET_BUDGET = tests_for_detection(BASE_DETECTION_P, TARGET)
LABELS = (
    "No overflow exposure", "Wrong lifecycle only", "Idealized SRI stub",
    "Packet-only oracle", "Too little random budget", "No replay evidence",
    "No enforced response",
)


def readiness_row(row: tuple[bool, ...], design: Design = Design()) -> dict:
    if len(row) != len(FACTORS) or any(type(value) is not bool for value in row):
        raise ValueError("A readiness row must contain seven Boolean factors")
    exposure, lifecycle, faithful, safety, budget, retain, respond = row
    stimulus = Stimulus(40000.0 if exposure else 20000.0, 20.0 if lifecycle else 50.0)
    actual_design = replace(design, software_in_loop=True)
    harness_design = replace(design, software_in_loop=faithful)
    actual = evaluate(stimulus, actual_design)
    observed = evaluate(stimulus, harness_design)
    oracle = "safety" if safety else "packet"
    detected = oracle_detects(observed, oracle)
    # Only the rare-tail model's high-BH/early-time region can fail these designs.
    p = BASE_DETECTION_P if detected else 0.0
    n = TARGET_BUDGET if budget else SHORT_BUDGET
    chance = detection_probability(p, n)
    replay = {
        "stimulus": asdict(stimulus),
        "design": asdict(harness_design),
        "oracle": oracle,
        "expected_detection": True,
    } if detected and retain else None
    return {
        "gates": dict(zip(FACTORS, row)),
        "stimulus": asdict(stimulus),
        "design": asdict(actual_design),
        "actual_navigation_loss": not actual.navigation_available,
        "harness_navigation_loss": not observed.navigation_available,
        "injected_control_detected": detected,
        "campaign_detection_p": p,
        "campaign_budget": n,
        "campaign_detection_probability": chance,
        "discovery_target_met": chance >= TARGET,
        "replay_case": replay,
        "modeled_response_blocks": replay is not None and respond,
        "response_target_met": chance >= TARGET and retain and respond,
    }


def readiness_experiment() -> dict:
    rows = [readiness_row(row) for row in product((False, True), repeat=len(FACTORS))]
    baseline = (True,) * len(FACTORS)
    controls = [{"name": "All prerequisites present", "removed_gate": None, **readiness_row(baseline)}]
    for index, (factor, label) in enumerate(zip(FACTORS, LABELS)):
        row = tuple(value if i != index else False for i, value in enumerate(baseline))
        controls.append({"name": label, "removed_gate": factor, **readiness_row(row)})
    controls.append({
        "name": "Guarded negative control", "removed_gate": None,
        **readiness_row(baseline, Design(conversion_guard=True)),
    })
    return {
        "schema_version": 1,
        "scope": "Synthetic prerequisite experiment; injected controls and analytic budgets, no additional Monte Carlo",
        "factors": list(FACTORS),
        "base_detection_p": BASE_DETECTION_P,
        "target_probability": TARGET,
        "short_budget": SHORT_BUDGET,
        "target_budget": TARGET_BUDGET,
        "equations": {
            "injected_detection": "E and L and F and O (fixed vulnerable design)",
            "replayable_finding": "injected_detection and R",
            "modeled_response": "injected_detection and R and A",
            "campaign_p": "0.0005 if E and L and F and O else 0 (specified rare-tail support)",
            "discovery_target": "1 - (1 - campaign_p)^n >= 0.95",
            "response_target": "discovery_target and R and A",
        },
        "summary": {
            "cases": len(rows),
            "actual_navigation_losses": sum(row["actual_navigation_loss"] for row in rows),
            "injected_detections": sum(row["injected_control_detected"] for row in rows),
            "replayable_findings": sum(row["replay_case"] is not None for row in rows),
            "modeled_response_blocks": sum(row["modeled_response_blocks"] for row in rows),
            "discovery_target_met": sum(row["discovery_target_met"] for row in rows),
            "response_target_met": sum(row["response_target_met"] for row in rows),
        },
        "ablations": controls,
        "rows": rows,
    }
