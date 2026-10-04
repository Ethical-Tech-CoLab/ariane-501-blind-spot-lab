export const defaultDesign = Object.freeze({
  alignment_retained: true,
  conversion_guard: false,
  isolate_alignment_failure: false,
  diagnostic_guard: false,
  software_in_loop: true,
  replicas: 2,
});

function finite(name, value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
}

export function convertInt16(value) {
  finite("BH", value);
  let integral = Math.trunc(value);
  if (Math.abs(value - integral) >= 0.5) integral += Math.sign(value);
  if (integral < -32768 || integral > 32767) {
    throw new RangeError("BH conversion exceeds signed 16-bit range");
  }
  return integral === 0 ? 0 : integral;
}

export function evaluate(stimulus, overrides = {}) {
  const { bh, time_s, alignment_end_s = 40 } = stimulus;
  for (const [name, value] of Object.entries({ bh, time_s, alignment_end_s })) {
    finite(name, value);
  }
  if (time_s < 0 || alignment_end_s < 0) throw new RangeError("Times must be nonnegative");
  const design = { ...defaultDesign, ...overrides };
  for (const name of Object.keys(defaultDesign).filter(name => name !== "replicas")) {
    if (typeof design[name] !== "boolean") throw new TypeError(`${name} must be boolean`);
  }
  if (!Number.isSafeInteger(design.replicas) || design.replicas < 1) {
    throw new RangeError("replicas must be a positive safe integer");
  }
  const active = design.alignment_retained && time_s < alignment_end_s;
  // The bounds include the ties-away rounding threshold; no physical BH scale is inferred.
  const outOfRange = active && design.software_in_loop && (bh >= 32767.5 || bh <= -32768.5);
  const exception = outOfRange && !design.conversion_guard;
  const halted = exception && !design.isolate_alignment_failure;
  const accepted = halted && !design.diagnostic_guard;
  return {
    conversion_out_of_range: outOfRange,
    alignment_exception: exception,
    failed_units: halted ? design.replicas : 0,
    navigation_available: !halted,
    diagnostic_accepted: accepted,
    unsafe_command: accepted,
    bus_frame_present: true,
  };
}

export function oracleDetects(outcome, oracle = "safety") {
  if (oracle === "safety") return !outcome.navigation_available || outcome.unsafe_command;
  if (oracle === "packet") return !outcome.bus_frame_present;
  throw new RangeError(`Unknown oracle: ${oracle}`);
}

export function compareEvaluation(stimulus, design, oracle) {
  const actual = evaluate(stimulus, { ...design, software_in_loop: true });
  const observed = evaluate(stimulus, design);
  return { actual, observed, detected: oracleDetects(observed, oracle) };
}

export function detectionProbability(p, n) {
  finite("p", p);
  if (p < 0 || p > 1) throw new RangeError("p must be between 0 and 1");
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError("n must be a nonnegative safe integer");
  if (n === 0 || p === 0) return 0;
  return p === 1 ? 1 : -Math.expm1(n * Math.log1p(-p));
}

export function budgetFor95(p) {
  detectionProbability(p, 1);
  if (p === 0) return null;
  if (p === 1) return 1;
  return Math.ceil(Math.log(0.05) / Math.log1p(-p));
}
