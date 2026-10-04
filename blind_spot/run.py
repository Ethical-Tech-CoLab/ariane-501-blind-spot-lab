"""Write or verify deterministic study results: python -m blind_spot.run."""

import argparse
import csv
from html import escape
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
                    raise SystemExit(f"Reproducibility check failed: {expected}")
        print("PASS: all seven generated result artifacts reproduce byte-for-byte.")
    else:
        results = generate(args.output)
        for row in results["monte_carlo"]:
            print(f'{row["name"]}: {row["detected"]}/{row["n"]} detections')


if __name__ == "__main__":
    main()
