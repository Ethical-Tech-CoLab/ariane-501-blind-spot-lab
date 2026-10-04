# Methods and model card

## Scope

This is a retrospective, mechanism-level teaching experiment. We knew the failure mechanism before selecting the model and distributions. It is not preregistered, a blind discovery test, an empirical launch-risk study, or a digital twin.

The simulator's outcome is **modeled navigation loss and/or an unsafe-command proxy**, not a physical breakup calculation. It has no aerodynamics, actual nozzle commands, guidance law, original diagnostic encodings, or original BH filter.

## Data provenance and missingness

[variables.csv](../data/variables.csv) separates documented facts, derived mathematics, invented experiment inputs, and unavailable historical quantities. Empty historical values mean unavailable, not zero. No missing telemetry is imputed.

The experiment generates complete finite input records. The model rejects nonfinite values, invalid times, invalid replica counts, and unknown profiles/oracles explicitly. Repeated Monte Carlo draws are permitted, not deduplicated; repetition belongs to iid sampling. The Boolean grid is checked to contain 256 unique rows. There is no supervised learning, fitting, training/test split, or normalization fitted to data.

## Conversion convention

The model converts a Python float to the nearest integer, with halfway values rounded away from zero, then checks the signed 16-bit range `[-32768, 32767]`. This follows the real-to-integer convention described in Ada RM 4.6. Python's default bankers' `round` would be inappropriate for that convention.

- `32767.49` rounds to 32767 and succeeds.
- `32767.5` rounds to 32768 and fails.
- `-32768.49` rounds to -32768 and succeeds.
- `-32768.5` rounds to -32769 and fails.

Tests include the immediately adjacent floating-point values and every representable signed 16-bit integer. The public inquiry does not provide the exact compiled instruction or complete subtype/scaling context, so this is **an illustrative Ada-style convention**, not a claimed bit-exact reconstruction. Integer-valued overflow examples remain overflow examples without relying on a half-unit rounding edge.

## State and causal structure

`time_s` is elapsed time after lift-off. For a retained alignment function, a conversion opportunity is active while `time_s < alignment_end_s`. The experiment fixes the latter to 40 seconds, a simplified form of the inquiry's approximately 40-second interval.

An out-of-range conversion in the implementation raises the modeled alignment exception unless explicitly guarded. Without exception isolation, all identical SRI replicas halt. Without diagnostic validation, the modeled diagnostic frame is accepted as flight information and produces an unsafe-command proxy.

The strong safety oracle flags missing navigation **or** an unsafe command. The deliberately weak oracle checks only whether a bus frame exists. Diagnostic frames therefore look like success to the weak oracle.

Removing post-launch alignment and guarding/isolating its conversion are separate modeled barriers. They are not certified repairs. In particular, the guard reports out-of-range status; it does not silently clamp BH and pretend navigation is correct.

An idealized SRI stub bypasses the failing code and returns nominal navigation. That is an intentionally inadequate **test harness**, not an improved implementation.

## Monte Carlo design

Every trial resets the toy system. It is one conversion opportunity, not a full trajectory or a full mission. BH and time are independent by construction; this is useful for demonstrating coverage but physically unrealistic.

| Profile | Synthetic BH distribution (conversion units) | Time distribution | Analytic detection p with default design |
|---|---|---|---:|
| legacy | Uniform [0, 30000] | Uniform [0, 80] seconds | 0 |
| expanded | Uniform [0, 65535] | Uniform [0, 80] seconds | 0.25 |
| rare_tail | 99.9% Uniform [0, 30000]; 0.1% Uniform [32768, 65535] | Uniform [0, 80] seconds | 0.0005 |

The expanded upper-conversion boundary is exactly the midpoint 32767.5; half the BH distribution overflows and half the times activate alignment. Thus `p = 1/2 * 1/2 = 1/4`. For the rare tail, `p = 0.001 * 1/2`.

These analytic values use ideal continuous distributions. Python's finite pseudorandom grid has negligible endpoint effects at these sample sizes. Boundary correctness is covered separately by deterministic tests rather than hoped for in random sampling.

No claim is made that historical BH was uniformly distributed, that time and BH were independent, or that Ariane 5's real failure was a rare stochastic fault. Conditional on the flown implementation and input history, the failure was systematic.

Seeds begin at 5011996. Matched expanded runs use the same seed and draw function. [study.json](../results/study.json) stores seeds, trial counts, settings, and counts; [monte_carlo.csv](../results/monte_carlo.csv) provides a flat table. Individual Monte Carlo draws are regenerated from seed rather than stored as a misleading telemetry dataset.

## Temporal demonstration

[synthetic_trace.csv](../results/synthetic_trace.csv) uses:

- `BH(t) = 50000 * t / 50`
- `t = 0, 0.1, ..., 50` seconds after lift-off
- alignment end at 40 seconds
- latched navigation loss once the modeled processor has halted.

It first crosses the upper conversion boundary at the sampled time 32.8 seconds. **This is not the historical 30-second failure time** and was not fitted to it. The default trace helper also supports a 72 ms step, inspired by the report's data-cycle period, but that is not the SRI's complete internal scheduler. No sub-cycle ordering between replicas is reconstructed.

![Synthetic temporal trace](../results/synthetic_trace.svg)

## Statistical inference

We report two-sided 95% Wilson intervals for observed detection proportions and an exact one-sided 95% upper binomial bound when detections equal zero:

`upper = 1 - 0.05^(1/n)`.

The approximately `3/n` shortcut is not used for computation. These intervals describe binomial sampling uncertainty, not uncertainty about the model's validity, omitted variables, or real-world deployment.

Under iid opportunities, detection by budget is `1 - (1-p)^n`. Solving for `n` yields:

`ceil(log(0.05) / log(1-p))`.

At `p=0` there is no finite budget; at `p=1` one test suffices. Stable `log1p` and `expm1` calculations avoid unnecessary numerical cancellation.

This is a demonstration, not hypothesis-test p-value fishing. We compare sample rates to independently derived probabilities and test implementation invariants. We do not infer a historical disaster probability from synthetic frequencies.

## Finite multivariate design

The eight Boolean factors form a full factorial 256-row design:

1. BH 20000 or 40000.
2. Time 50 or 20 seconds.
3. Retained alignment.
4. Conversion guard.
5. Alignment exception isolation.
6. Diagnostic validation.
7. Implementation in the test loop.
8. Safety rather than packet oracle.

Full pairwise coverage means all `C(8,2) * 4 = 112` value pairs. A deterministic greedy algorithm generates one covering suite. A second suite uses only non-navigation-loss candidates but must still cover the **same full pair universe**. The tests verify this constructively, rather than merely trusting a reported coverage percentage.

Navigation loss in this design requires six simultaneous factor settings; oracle detection adds another. This is a pedagogical consequence of the design/harness dimensions, not a historical estimate of interaction order.

No pairwise method, sample size, or finite full-factorial grid can prove completeness over unspecified variables, continuous values, arbitrary event sequences, or an incorrect model.

## Detection-readiness experiment

This extends the support/harness/oracle contrasts with **deterministic controls and exact analytic budgets**, not additional Monte Carlo draws. The six seeded runs, their seeds, and their total 1,600,000 opportunities are unchanged. The eight-factor design above tests design/harness interactions; this separate seven-switch design tests the path from exposure to a replayable finding and a modeled release response.

The seven binary inputs are complete, intentionally crossed design records. No historical data are imputed. All 128 rows are unique; the nine named controls are selected illustrations, not additional independent samples.

| Symbol | Switch | Enabled | Disabled |
|---|---|---|---|
| E | Overflow support | Inject BH 40000; random campaign uses the published rare-tail mixture | Inject BH 20000; campaign BH confined to non-overflow support |
| L | Alignment reachable | Inject at 20 s; campaign time uniform [0,80] s | Inject at 50 s; campaign time restricted to [40,80] s |
| F | Implementation in loop | Existing conversion and exception semantics | Idealized nominal-output stub |
| O | Safety oracle | Missing navigation OR unsafe command | Packet presence only |
| B | Adequate random budget | `tests_for_detection(0.0005, 0.95)` = 5,990 | 10 |
| R | Retain replay evidence | Save stimulus, design settings, oracle, expected failure | Do not retain the finding's replay record |
| A | Enforce response | A retained detected finding blocks under a Boolean policy | Detection has no modeled release consequence |

The implementation design retains alignment, leaves conversion unguarded and unisolated, accepts diagnostics, and uses two identical replicas. It is held fixed across the one-at-a-time prerequisite removals. A separate protected negative control enables the conversion guard while keeping all seven switches true. This is a control against blanket failure reporting, not a flight-certified repair.

### Exact gate conditions

For the fixed vulnerable design, define:

```text
actual navigation loss in injected case = E AND L
harness navigation loss                = E AND L AND F
D (injected witness detected)          = E AND L AND F AND O
replayable finding                     = D AND R
modeled response block                 = D AND R AND A
```

The first four switches are jointly necessary and sufficient for **this injected dynamic witness**, not for every possible discovery technique. Two replicas do not make the events independent. Rejecting diagnostics alone would still trigger the safety oracle because navigation remains unavailable.

For the separate **specified iid random campaign**:

```text
p = 0.001 * 0.5 = 0.0005 when E, L, F, O are enabled; otherwise 0
n = 5990 when B is enabled; otherwise 10
q = 1 - (1 - p)^n
discovery target met = q >= 0.95
response target met  = (q >= 0.95) AND R AND A
```

The 0.001 overflow-tail weight and independent one-half active-time probability come from the existing rare-tail design. Disabled E or L removes joint support; disabled F or O removes detection. This formula is conditional on that construction; real dependencies, sampling without replacement, adaptive stopping, and uncertain tail probabilities require different analysis. The guard in the protected control removes the event, so its detection `p=0`, not 0.0005.

The injected witness is intentionally selected, **not one of the random campaign draws**. Its detection therefore does not depend on B. At `p=0.0005`, 10 random tests give approximately 0.00498876498688 probability of detection. The first budget meeting 0.95 is 5,990; the immediately preceding budget fails the target. That minimal-threshold property is checked numerically, not inferred from rounded display values.

R and A do not change `p`, the injected detection, or the physical model. `response_target_met` describes the conditional probability target for the *defined* response chain, assuming the retention/policy switches do what they say. It does not measure a person's understanding, operational response reliability, or organizational behavior. Missing evidence is represented by `null`, not a fabricated replay.

### Execution, controls, and falsification

[readiness.py](../blind_spot/readiness.py) evaluates every control using the existing [mechanism model](../blind_spot/model.py). The complete grid and all retained witnesses are published under `detection_readiness` in [study.json](../results/study.json). [The summary](../results/summary.md#detection-prerequisites-controlled-removals) and [control chart](../results/detection_readiness.svg) are generated from that record.

Tests independently check the logical conditions for every row, one-factor changes in the named controls, the minimal budget threshold, and each saved witness by reconstructing and executing its stimulus/design/oracle. They also cross the detection gates with retention/removal, conversion guarding, exception isolation, and diagnostic rejection from the existing design. A stub or packet oracle must mask the positive case; the faithful safety oracle must detect it; the guarded negative control must not.

For actual release-style behavior rather than a Boolean response proxy, the existing `python -m blind_spot.check_contract --design baseline` returns exit code 1 for the known violations, while `--design alignment-removed` returns 0. That executable contrast is useful evidence of a gate, but is not evidence a real organization will enforce it.

## Reproducibility and verification

- Unit tests: conversion boundaries, all 65,536 representable integers, phase boundary, redundant common-mode failure, fault containment, diagnostic handling, probability formulas, invalid inputs, and actual pair coverage.
- Release-style contract: `python -m blind_spot.check_contract --design baseline` exits 1 for two boundary violations; `--design alignment-removed` exits 0. The test suite verifies these expected contrasting outcomes.
- Result verification: recompute and byte-compare all eight generated artifacts.
- Artifact checks: analytic rates versus observed counts, matched input counts, scenario completeness, source/assumption traceability, parseable SVG/CSV/JSON, and notebook structure.
- Notebook: recomputes the study, compares with published results, displays figures and interprets each code cell.
- Prerequisite verification: all 128 process-gate combinations, nine named controls, saved-case replay, exact budget threshold, and separate detection/evidence/response outcomes.
- CI: repeats tests, result verification, and notebook execution on Python 3.12.

The Windows lock file captures the original optional notebook environment. The simulation itself uses no third-party numerical libraries. Independent Linux CI initially exposed last-bit differences in `expm1`-derived probabilities (for example, 0.6321207427683548 versus 0.632120742768355). Counts, scenarios and conclusions were identical.

Computed probabilities and interval bounds are therefore published at **12 significant digits**, explicitly recorded in the result metadata. Internal statistical calculations retain full floating-point precision; integer counts and sample settings are unchanged. Regression tests check both that the observed platform noise disappears and that meaningful probability changes remain visible. Byte-for-byte checks still compare every generated artifact rather than silently accepting arbitrary differences.
