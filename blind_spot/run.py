"""Write or verify deterministic study results: python -m blind_spot.run."""

import argparse
import csv
from difflib import unified_diff
from html import escape
from itertools import islice
import json
import math
from pathlib import Path
import tempfile

from .experiments import run_study
from .model import Design, synthetic_trace
from .statistics import detection_probability


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def svg_frame(title: str, description: str, elements: list[str], height: int = 510) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {height}" role="img" '
        'aria-labelledby="title description">\n'
        f'<title id="title">{escape(title)}</title><desc id="description">{escape(description)}</desc>\n'
        '<rect width="100%" height="100%" fill="#f8fafc"/>\n'
        '<g font-family="Arial, sans-serif" fill="#0f172a">\n'
        f'<text x="35" y="38" font-size="23" font-weight="bold">{escape(title)}</text>\n'
        + "\n".join(elements) + "\n</g></svg>\n"
    )


def monte_carlo_chart(results: dict) -> str:
    colors = ("#475569", "#2563eb", "#7c3aed", "#d97706", "#dc2626", "#059669")
    elements = [
        '<text x="35" y="64" font-size="14">Synthetic input distributions; NOT launch failure probabilities. Bar scale: 0 to 30%.</text>'
    ]
    for i, (row, color) in enumerate(zip(results["monte_carlo"], colors)):
        y = 108 + i * 58
        low, high = row["wilson_95"]
        left, scale = 340, 1400
        width = scale * row["detected_rate"]
        elements.extend([
            f'<text x="35" y="{y + 5}" font-size="15">{escape(row["name"])}</text>',
            f'<rect x="{left}" y="{y - 14}" width="420" height="24" fill="#e2e8f0"/>',
            f'<rect x="{left}" y="{y - 14}" width="{width:.3f}" height="24" fill="{color}"/>',
            f'<line x1="{left + scale * low:.3f}" x2="{left + scale * high:.3f}" y1="{y - 2}" y2="{y - 2}" stroke="#0f172a" stroke-width="3"/>',
            f'<text x="780" y="{y + 4}" font-size="14">{row["detected"]:,}/{row["n"]:,}</text>',
        ])
    elements.append('<text x="35" y="477" font-size="14">Black marks: 95% Wilson intervals. Tiny rare-tail bars are quantified in the results table.</text>')
    return svg_frame("A million green tests can miss an out-of-profile bug", "Detected failures under six synthetic test configurations.", elements)


def detection_chart() -> str:
    elements = [
        '<text x="35" y="64" font-size="14">P(at least one detection) = 1 - (1 - p)^n. Independent opportunities; p is assumed.</text>'
    ]
    for value in (0, 0.25, 0.5, 0.75, 1):
        y = 390 - value * 290
        elements.extend([
            f'<line x1="95" x2="920" y1="{y}" y2="{y}" stroke="#cbd5e1"/>',
            f'<text x="40" y="{y + 5}" font-size="14">{value:.0%}</text>',
        ])
    for exponent in range(7):
        x = 95 + exponent / 6 * 825
        elements.append(f'<text x="{x}" y="416" text-anchor="middle" font-size="14">10^{exponent}</text>')
    for i, (p, color) in enumerate(((0.25, "#2563eb"), (0.0005, "#7c3aed"), (0.000001, "#d97706"), (0.0, "#dc2626"))):
        points = []
        for index in range(181):
            n = max(1, round(10 ** (index / 30)))
            points.append(f"{95 + math.log10(n) / 6 * 825:.2f},{390 - 290 * detection_probability(p, n):.2f}")
        elements.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>')
        elements.append(f'<text x="{100 + i * 220}" y="465" font-size="15" fill="{color}">p = {p:g}</text>')
    elements.append('<text x="420" y="441" font-size="14">Test budget (log scale)</text>')
    return svg_frame("More tests help only when exposure is nonzero", "Detection probability against test budget for four assumed probabilities.", elements)


def trace_chart(rows: list[dict]) -> str:
    elements = [
        '<text x="35" y="64" font-size="14">Invented linear BH ramp, not measured flight telemetry. Time is seconds after lift-off.</text>'
    ]
    for key, color in (("bh", "#2563eb"),):
        points = " ".join(
            f'{95 + row["time_s"] / 50 * 825:.2f},{390 - row[key] / 50000 * 290:.2f}' for row in rows
        )
        elements.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>')
    threshold_y = 390 - 32767.5 / 50000 * 290
    elements.extend([
        f'<line x1="95" x2="920" y1="{threshold_y}" y2="{threshold_y}" stroke="#dc2626" stroke-width="2" stroke-dasharray="6 4"/>',
        f'<text x="480" y="{threshold_y - 12}" font-size="15" fill="#dc2626">Upper conversion boundary: 32767.5</text>',
        '<text x="95" y="430" font-size="14">0 s</text><text x="885" y="430" font-size="14">50 s</text>',
        '<text x="35" y="390" font-size="14">0</text><text x="15" y="104" font-size="14">50000</text>',
        '<text x="35" y="474" font-size="14">Failure remains latched after alignment ends at 40 s; removing alignment preserves modeled navigation.</text>',
    ])
    return svg_frame("A boundary-crossing trace exposes the mechanism", "Synthetic BH rises linearly through the conversion boundary.", elements)


def readiness_chart(readiness: dict) -> str:
    columns = ["E", "L", "F", "O", "B", "R", "A", "Detect", "95%", "Block"]
    elements = [
        '<text x="35" y="65" font-size="14">Injected controls + analytic rare-tail budgets. No new Monte Carlo; no measured AI discovery rate.</text>',
    ]
    for index, label in enumerate(columns):
        elements.append(f'<text x="{350 + index * 60}" y="102" text-anchor="middle" font-size="14">{label}</text>')
    for i, row in enumerate(readiness["ablations"]):
        y = 139 + i * 40
        elements.append(f'<text x="35" y="{y + 5}" font-size="14">{escape(row["name"])}</text>')
        values = [row["gates"][key] for key in readiness["factors"]]
        values += [row["injected_control_detected"], row["discovery_target_met"], row["modeled_response_blocks"]]
        for index, value in enumerate(values):
            color = ("#2563eb" if index < 7 else "#7c3aed" if index < 9 else "#d97706") if value else "#e2e8f0"
            text_color = "#ffffff" if value else "#475569"
            x = 350 + index * 60
            elements.append(f'<rect x="{x - 18}" y="{y - 14}" width="36" height="27" rx="4" fill="{color}"/>')
            elements.append(f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="14" fill="{text_color}">{int(value)}</text>')
    elements.extend([
        '<text x="35" y="506" font-size="13">1 = enabled/true; 0 = disabled/false. Detect = injected case. 95% = random-campaign target.</text>',
        '<text x="35" y="531" font-size="13">E exposure; L lifecycle; F fidelity; O oracle; B budget; R replay retained; A response enforced.</text>',
        '<text x="35" y="556" font-size="13">Block = modeled response to a retained finding, not a measured human action or certification.</text>',
    ])
    return svg_frame("What has to be true for a failure to become actionable?",
                     "Seven prerequisite switches, one-at-a-time removals and a guarded negative control. "
                     "Short budgets still detect injected faults; missing replay or response does not erase detection.",
                     elements, height=580)


def summary_markdown(results: dict) -> str:
    lines = [
        "# Generated results", "",
        "All rates describe synthetic test opportunities, NOT historical flight risk.",
        "Seeds, settings, complete Boolean suites and analytic comparisons are in [study.json](study.json).",
        "", "| Experiment | Trials | Latent triggers | Navigation losses | Detected | Rate | Wilson 95% interval |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in results["monte_carlo"]:
        low, high = row["wilson_95"]
        lines.append(
            f'| {row["name"]} | {row["n"]:,} | {row["latent_triggers"]:,} | '
            f'{row["navigation_losses"]:,} | {row["detected"]:,} | {row["detected_rate"]:.6%} | '
            f'[{low:.6%}, {high:.6%}] |'
        )
    lines.extend([
        "", "## Conditional detection budgets", "",
        "| Assumed per-test detection p | Tests for at least 95% detection probability |",
        "|---:|---:|",
    ])
    for row in results["probability_table"]:
        count = row["tests_for_95_percent"]
        lines.append(f'| {row["p"]:g} | {count if count is not None else "No finite budget"} |')
    lines.extend(["", "## Multivariate coverage", "", "| Suite | Cases | Pair coverage | Navigation losses | Detected |", "|---|---:|---:|---:|---:|"])
    for name, row in results["coverage"]["suites"].items():
        lines.append(f'| {name} | {row["cases"]} | {row["pair_coverage"]:.0%} | {row["navigation_losses"]} | {row["detected"]} |')
    lines.extend([
        "", "The blind witness is deliberately constructed from non-failing candidates.",
        "It proves that 100% pairwise coverage does not imply detection; it does not estimate typical pairwise effectiveness.",
        "", "## Barrier ablations", "",
        "| Change | Failed units | Navigation available | Unsafe command | Safety oracle detects |",
        "|---|---:|---|---|---|",
    ])
    for row in results["ablations"]:
        lines.append(f'| {row["name"]} | {row["failed_units"]} | {row["navigation_available"]} | {row["unsafe_command"]} | {row["detected"]} |')
    readiness = results["detection_readiness"]
    summary = readiness["summary"]
    lines.extend([
        "", "## Detection prerequisites: controlled removals", "",
        "One known injected case is distinct from a random campaign. The design stays vulnerable except for the guarded negative control.",
        "The existing matched Monte Carlo runs establish support/harness/oracle contrasts; this experiment adds deterministic process controls, not random draws.",
        "", "| Control | Actual navigation loss | Injected case detected | Random budget | P(at least one detection) | 95% target met | Replay retained | Modeled response blocks |",
        "|---|---|---|---:|---:|---|---|---|",
    ])
    for row in readiness["ablations"]:
        lines.append(
            f'| {row["name"]} | {row["actual_navigation_loss"]} | {row["injected_control_detected"]} | '
            f'{row["campaign_budget"]:,} | {row["campaign_detection_probability"]:.6%} | '
            f'{row["discovery_target_met"]} | {row["replay_case"] is not None} | {row["modeled_response_blocks"]} |'
        )
    lines.extend([
        "", "![Controlled prerequisite removals](detection_readiness.svg)", "",
        f'The complete seven-switch grid has **{summary["cases"]}** distinct configurations: '
        f'**{summary["actual_navigation_losses"]}** actual navigation losses, '
        f'**{summary["injected_detections"]}** injected detections, '
        f'**{summary["replayable_findings"]}** replayable findings, and '
        f'**{summary["modeled_response_blocks"]}** modeled response blocks.',
        f'**{summary["discovery_target_met"]}** configurations meet the conditional 95% discovery target; '
        f'**{summary["response_target_met"]}** also retains evidence and enforces the modeled response.',
        "These counts enumerate a designed truth table, not an empirical readiness score, probability of human response, or AI discovery rate.",
        f'With the specified rare-tail detection p={readiness["base_detection_p"]:g}, '
        f'the minimal 95% budget is **{readiness["target_budget"]:,}**. A smaller budget can still detect a fault; '
        "it does not meet that target. Replay retention and response policy are downstream of detection.",
        "The executable core has not changed. The protected negative control prevents this modeled failure even with all test prerequisites enabled.",
        "Exact equations, replayable cases, and all rows are in [study.json](study.json); "
        "see [methods](../docs/METHODS.md#detection-readiness-experiment) and the "
        "[future-testing guide](../docs/FRAMEWORK.md#design-a-detection-readiness-experiment).",
    ])
    lines.extend([
        "", "## Interpretation", "",
        "The expanded, idealized and packet-oracle runs use identical inputs and seeds. A stub removes the modeled bug; a weak oracle conceals the failure.",
        "For zero detections in 1,000,000 iid trials, the exact one-sided 95% upper bound is",
        f'{results["monte_carlo"][0]["zero_failure_upper_95"]:.12g} **under that test distribution only**.',
        "For masked-oracle runs, an interval on detected events is not an interval on actual failures.",
        "No flight telemetry, original Ada binary, calibrated BH model, or blinded AI evaluation is present.",
        "",
    ])
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def generate(output: Path) -> dict:
    results = run_study()
    output.mkdir(parents=True, exist_ok=True)
    write_text(output / "study.json", json.dumps(results, indent=2, allow_nan=False) + "\n")
    fields = (
        "name", "profile", "n", "seed", "expected_detection_p", "latent_triggers",
        "navigation_losses", "unsafe_commands", "detected", "detected_rate",
    )
    write_csv(output / "monte_carlo.csv", [{key: row[key] for key in fields} for row in results["monte_carlo"]])
    trace = synthetic_trace(50000.0, duration_s=50.0, step_s=0.1)
    fixed = synthetic_trace(50000.0, Design(alignment_retained=False), duration_s=50.0, step_s=0.1)
    for row, repaired in zip(trace, fixed):
        row["navigation_with_alignment_removed"] = repaired["navigation_available"]
    write_csv(output / "synthetic_trace.csv", trace)
    write_text(output / "summary.md", summary_markdown(results))
    write_text(output / "monte_carlo.svg", monte_carlo_chart(results))
    write_text(output / "detection_probability.svg", detection_chart())
    write_text(output / "synthetic_trace.svg", trace_chart(trace))
    write_text(output / "detection_readiness.svg", readiness_chart(results["detection_readiness"]))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--check", action="store_true", help="Recompute and compare without changing committed artifacts")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="ariane501-check-") as temporary:
            generated = Path(temporary)
            generate(generated)
            for path in sorted(generated.iterdir()):
                expected = args.output / path.name
                if not expected.is_file() or expected.read_bytes() != path.read_bytes():
                    if expected.is_file():
                        difference = unified_diff(
                            expected.read_text(encoding="utf-8").splitlines(),
                            path.read_text(encoding="utf-8").splitlines(),
                            fromfile="published", tofile="recomputed", n=1,
                        )
                        for line in islice(difference, 60):
                            print(line[:240])
                    raise SystemExit(f"Reproducibility check failed: {expected}")
        print("PASS: all eight generated result artifacts reproduce byte-for-byte.")
    else:
        results = generate(args.output)
        for row in results["monte_carlo"]:
            print(f'{row["name"]}: {row["detected"]}/{row["n"]} detections')


if __name__ == "__main__":
    main()
