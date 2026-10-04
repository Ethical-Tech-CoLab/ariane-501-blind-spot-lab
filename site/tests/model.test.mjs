import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  convertInt16, evaluate, oracleDetects, compareEvaluation,
  detectionProbability, budgetFor95,
} from "../model.mjs";

const published = JSON.parse(await readFile(new URL("../../results/study.json", import.meta.url), "utf8"));
const stimulus = { bh: 40000, time_s: 20 };
const keys = ["conversion_out_of_range", "alignment_exception", "failed_units",
  "navigation_available", "diagnostic_accepted", "unsafe_command", "bus_frame_present"];

function adjacent(value, direction) {
  const buffer = new ArrayBuffer(8);
  const view = new DataView(buffer);
  view.setFloat64(0, value);
  const bits = view.getBigUint64(0);
  view.setBigUint64(0, bits + (value * direction > 0 ? 1n : -1n));
  return view.getFloat64(0);
}

test("Ada-style nearest ties-away conversion, including representable adjacent values", () => {
  for (const [input, expected] of [[32767.49, 32767], [-32768.49, -32768],
    [0.5, 1], [-0.5, -1], [0, 0], [-0, 0],
    [adjacent(32767.5, -1), 32767], [adjacent(-32768.5, 1), -32768]]) {
    assert.equal(convertInt16(input), expected);
  }
  for (const value of [32767.5, -32768.5, adjacent(32767.5, 1), adjacent(-32768.5, -1), 40000]) {
    assert.throws(() => convertInt16(value), RangeError);
  }
  for (let value = -32768; value <= 32767; value++) assert.equal(convertInt16(value), value);
});

test("modeled range predicate agrees with conversion at both boundaries", () => {
  for (const value of [-32768.5, adjacent(-32768.5, 1), -32768.49,
    32767.49, adjacent(32767.5, -1), 32767.5, adjacent(32767.5, 1)]) {
    let overflow = false;
    try { convertInt16(value); } catch (error) {
      assert.ok(error instanceof RangeError);
      overflow = true;
    }
    assert.equal(evaluate({ bh: value, time_s: 0 }).conversion_out_of_range, overflow);
  }
});

test("lifecycle cutoff is exclusive; removing alignment blocks the path", () => {
  assert.equal(evaluate({ bh: 40000, time_s: 0 }).failed_units, 2);
  assert.equal(evaluate({ bh: 40000, time_s: adjacent(40, -1) }).failed_units, 2);
  assert.equal(evaluate({ bh: 40000, time_s: 40 }).failed_units, 0);
  assert.equal(evaluate({ bh: 40000, time_s: 80 }).failed_units, 0);
  assert.equal(evaluate({ bh: 40000, time_s: 0, alignment_end_s: 0 }).failed_units, 0);
  assert.equal(evaluate(stimulus, { alignment_retained: false }).failed_units, 0);
});

test("every identical replica shares the deterministic failure", () => {
  for (const replicas of [1, 2, 3, 10]) {
    const outcome = evaluate(stimulus, { replicas });
    assert.equal(outcome.failed_units, replicas);
    assert.equal(outcome.navigation_available, false);
  }
});

test("range guarding and exception isolation preserve distinct intermediate states", () => {
  const guarded = evaluate(stimulus, { conversion_guard: true });
  assert.equal(guarded.conversion_out_of_range, true);
  assert.equal(guarded.alignment_exception, false);
  assert.equal(guarded.navigation_available, true);
  const isolated = evaluate(stimulus, { isolate_alignment_failure: true });
  assert.equal(isolated.conversion_out_of_range, true);
  assert.equal(isolated.alignment_exception, true);
  assert.equal(isolated.navigation_available, true);
});

test("rejecting diagnostics is not navigation repair, and the weak oracle stays blind", () => {
  const outcome = evaluate(stimulus, { diagnostic_guard: true });
  assert.equal(outcome.navigation_available, false);
  assert.equal(outcome.diagnostic_accepted, false);
  assert.equal(outcome.unsafe_command, false);
  assert.equal(oracleDetects(outcome, "safety"), true);
  assert.equal(oracleDetects(outcome, "packet"), false);
  const baseline = evaluate(stimulus);
  assert.equal(baseline.bus_frame_present, true);
  assert.equal(baseline.unsafe_command, true);
  assert.equal(oracleDetects(baseline, "packet"), false);
});

test("test harness and oracle cannot rewrite the displayed implementation outcome", () => {
  const stub = compareEvaluation(stimulus, { software_in_loop: false }, "safety");
  assert.equal(stub.actual.navigation_available, false);
  assert.equal(stub.observed.navigation_available, true);
  assert.equal(stub.detected, false);
  const weak = compareEvaluation(stimulus, { software_in_loop: true }, "packet");
  assert.deepEqual(weak.actual, weak.observed);
  assert.equal(weak.actual.navigation_available, false);
  assert.equal(weak.detected, false);
});

test("JavaScript outcomes match all published Python barrier ablations", () => {
  const settings = {
    baseline_identical_pair: {}, one_unit: { replicas: 1 }, three_identical_units: { replicas: 3 },
    remove_postlaunch_alignment: { alignment_retained: false },
    guard_alignment_conversion: { conversion_guard: true },
    isolate_alignment_exception: { isolate_alignment_failure: true },
    reject_diagnostic_frame: { diagnostic_guard: true },
    idealized_sri_stub: { software_in_loop: false },
  };
  assert.equal(published.ablations.length, Object.keys(settings).length);
  for (const row of published.ablations) {
    assert.ok(Object.hasOwn(settings, row.name), `Missing parity case: ${row.name}`);
    const outcome = evaluate(stimulus, settings[row.name]);
    assert.deepEqual(outcome, Object.fromEntries(keys.map(key => [key, row[key]])), row.name);
    assert.equal(oracleDetects(outcome), row.detected, row.name);
  }
});

test("all 256 Boolean configurations reproduce published loss/detection totals", () => {
  let losses = 0;
  let detected = 0;
  const seen = new Set();
  for (let mask = 0; mask < 256; mask++) {
    const bits = Array.from({ length: 8 }, (_, bit) => Boolean(mask & (1 << bit)));
    seen.add(bits.join(","));
    const [high, early, retained, guard, isolate, diagnostic, implementation, safety] = bits;
    const outcome = evaluate({ bh: high ? 40000 : 20000, time_s: early ? 20 : 50 }, {
      alignment_retained: retained, conversion_guard: guard, isolate_alignment_failure: isolate,
      diagnostic_guard: diagnostic, software_in_loop: implementation,
    });
    losses += Number(!outcome.navigation_available);
    detected += Number(oracleDetects(outcome, safety ? "safety" : "packet"));
  }
  const grid = published.coverage.suites.exhaustive;
  assert.equal(seen.size, grid.cases);
  assert.equal(losses, grid.navigation_losses);
  assert.equal(detected, grid.detected);
});

test("stable analytic budget calculator matches published Python probabilities", () => {
  assert.equal(detectionProbability(0, 1000000), 0);
  assert.equal(detectionProbability(1, 0), 0);
  assert.equal(detectionProbability(1, 1), 1);
  assert.equal(budgetFor95(0), null);
  assert.equal(budgetFor95(1), 1);
  for (const row of published.probability_table) {
    assert.equal(budgetFor95(row.p), row.tests_for_95_percent);
    for (const [n, probability] of Object.entries(row.detection_by_budget)) {
      assert.ok(Math.abs(detectionProbability(row.p, Number(n)) - probability) <= Math.max(1e-15, probability * 1e-11));
    }
    if (row.tests_for_95_percent !== null) {
      assert.ok(detectionProbability(row.p, row.tests_for_95_percent) >= 0.95);
      assert.ok(detectionProbability(row.p, row.tests_for_95_percent - 1) < 0.95);
    }
  }
});

test("invalid inputs are rejected rather than shown as green defaults", () => {
  for (const bh of [NaN, Infinity, -Infinity, true, "40000", null]) {
    assert.throws(() => convertInt16(bh));
    assert.throws(() => evaluate({ bh, time_s: 20 }));
  }
  for (const time of [-1, NaN, "20"]) assert.throws(() => evaluate({ bh: 0, time_s: time }));
  for (const replicas of [0, -1, 1.5, true, "2"]) assert.throws(() => evaluate(stimulus, { replicas }));
  assert.throws(() => evaluate(stimulus, { conversion_guard: 1 }));
  assert.throws(() => oracleDetects(evaluate(stimulus), "unknown"));
  for (const p of [-1, 1.1, NaN]) assert.throws(() => detectionProbability(p, 10));
  for (const n of [-1, 0.5, Infinity, "100"]) assert.throws(() => detectionProbability(0.1, n));
});
