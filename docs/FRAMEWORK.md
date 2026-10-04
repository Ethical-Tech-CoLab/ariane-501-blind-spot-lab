# BLIND-SPOT: an assumption-challenging evaluation framework

**Goal:** reduce blind spots, not promise to eliminate unknown unknowns.

This is a reusable evaluation method with one executable case study. It is not a generic simulator that magically understands arbitrary systems.

## The nine steps

| Step | Required artifact | Ariane example | AI-engineered-system example |
|---|---|---|---|
| **B - Bound the claim** | Intended use, environment, guarantee, exclusions | Valid navigation through the new flight envelope | Correct, authorized task completion with real tools |
| **L - List assumptions** | Versioned assumption register with owners and evidence | BH stays representable; alignment can remain active | Tool output schema, context size, user authority |
| **I - Identify dependencies** | Dependency and shared-failure map | Both SRIs run the same code | Agents share a model, prompt, retrieval corpus, or evaluator |
| **N - Negate assumptions** | Concrete falsifiers and nearby boundary cases | BH exceeds range during alignment | Tool returns error text with HTTP 200; context shifts |
| **D - Diversify evidence** | Boundary, static, sequence, combinatorial, random and replay tests | Exercise real SRI logic with new trajectory inputs | Exercise real orchestration and failure paths, not only mocks |
| **S - Specify the oracle** | Safety and availability properties; negative controls | Diagnostics are not flight data; navigation remains available | Error responses are not successful actions; refusals are scored correctly |
| **P - Probe the test world** | Simulator-fidelity and sampling-support review | Does the SRI model even contain the overflow? | Does a mocked tool hide real parser, state, latency, or permission failures? |
| **O - Own uncertainty** | Explicit unknowns, residual risk, release blockers | Missing BH calibration prevents flight-level claims | Unknown distribution shift prevents deployment-wide reliability claims |
| **T - Track change** | Invalidation triggers and regression evidence | Requalification when moving from Ariane 4 to Ariane 5 | Re-evaluate on model, tool, prompt, data, policy or deployment changes |

Do not shorten the process to "generate more tests."

## Executable assumption register

Start with [assumptions.json](../data/assumptions.json). Each record carries:

- a falsifiable claim, not "the system is robust";
- owner and evidence references;
- scope and invalidation trigger;
- a concrete falsifier;
- a test mapping;
- a known/assumed/unknown status;
- the consequence of being wrong.

For other projects, replace the domain facts and connect the test mappings to the actual system. An assumption without a test or independent evidence is an open obligation, not automatically false and not automatically safe.

## Turn assumptions into contracts

Write `Assumption(environment) => Guarantee(component)`, then separately test whether the deployed environment satisfies the assumption.

For Ariane's alignment conversion:

- Local contract: if rounded BH fits the target representation, the conversion succeeds.
- Environmental obligation: all reachable values during every phase where the function executes fit that representation.
- System obligation: an alignment failure must not disable essential navigation, and diagnostics must not be interpreted as valid navigation.

Checking only the local contract would not establish the other two obligations. Even a formal proof remains conditional on the model and assumptions it proves against.

## Critical and supposedly noncritical settings

Classify criticality by **reachable consequences**, not by the label attached to a module. Pre-launch alignment looked irrelevant after lift-off, but shared processor and exception policy made it mission-critical.

Inventory at least:

| Dimension | Useful partitions |
|---|---|
| Numeric representations | min/max, just inside/outside, half-integer boundaries, units and scale |
| Lifecycle | startup, transition, nominal operation, hold, resume, shutdown |
| Time and ordering | timeout, stale input, simultaneous failures, recovery and re-entry |
| Interfaces | valid payload, explicit error, malformed payload, stale or diagnostic frame |
| Dependencies | shared code, shared state, shared hardware, shared failure detector |
| Environment | new operating envelope, units, distribution shift, rate and load |
| Recovery | retries, degraded service, retained state, unavailable backup |
| Test apparatus | mocked versus real implementation, logging, instrumentation, oracle |
| Configuration | defaults, feature flags, ignored/unused settings, compatibility settings |

Treat apparently irrelevant variables as review candidates. Do not invent a physical effect just to give every variable a coefficient. Document why a variable is excluded, what evidence supports exclusion, and what change would invalidate it.

The present lab does **not** simulate weather, payload mass, vibration, processor timing, or every configuration. The inquiry found several external conditions irrelevant to this accident; a different system may not. Exhaustiveness is claimed only for the published eight-factor grid.

## Use methods in layers

1. **Deterministic boundary tests first.** They are inexpensive and exact for known representation limits.
2. **Static/range reasoning.** Check whether all reachable states satisfy the contract; avoid proofs whose preconditions simply restate the desired conclusion.
3. **Stateful sequence tests.** Include lifecycle transitions and failure latching, not only independent snapshots.
4. **Constrained combinatorial testing.** Select interaction strength from the hazards; validate actual coverage. Pairwise is not magic.
5. **Monte Carlo.** Separate realistic operational sampling from stress sampling. Publish distributions, dependency structure, seeds and budgets.
6. **Importance/adaptive search when necessary.** If stress sampling is used to estimate real-world risk, use justified weights and uncertainty. This lab does not claim such an estimate.
7. **Implementation-in-the-loop replay.** Verify that simplified models expose the failure modes they are meant to test.
8. **Independent review and falsifier generation.** Have people with different assumptions challenge the model boundary, not just its test count.

For unknown historical inputs, record an epistemic gap. Randomizing a guessed range does not turn missing knowledge into measured uncertainty.

## Suggested release gates

Use the gates proportionately to consequence; these are not a certification standard.

- Every critical assumption has an owner and independently reviewable justification.
- New environments trigger revalidation; prior pass rates are not silently transferred.
- Safety and availability properties are evaluated separately.
- Known negative controls fail the relevant oracle.
- Real implementation paths and shared-failure dependencies are exercised.
- Sampling support, excluded regions, and combinatorial/sequence coverage are reported.
- Unresolved model-fidelity or critical-range gaps are release blockers or receive explicit accountable risk acceptance, never a green default.
- Post-deployment monitoring detects invalid assumptions and has a defined response.

## Design a detection-readiness experiment

Start with the question: **what would have to be true for this failure mode to be uncovered, and what would make the finding actionable?** Do not start by choosing a large test count.

### 1. State the hypothesis and the decision

Name the failure class, deployed environment, required service, and release consequence. For an AI tool workflow, a concrete hypothesis might be: "a malformed tool result can be accepted as completed work during retry recovery." Define failure independently of the implementation's success flag. Do not claim that this lab discovered that example empirically.

Specify two endpoints: **detection of a real contract violation** and **an evidence-backed response to it**. Passing an evaluation and blocking release are different observables. An intentionally broken control is evidence about the detector, not the deployment's defect rate.

### 2. Build an executable positive control and a protected negative control

Construct a minimal input/state sequence known to violate the contract and a comparable case that must not. Exercise actual integration code where feasible. If some parts remain simulated, list exactly which failure semantics the simulator preserves and verify them against an independent reference.

In this lab, BH 40000 at 20 s exposes the existing conversion chain; guarding that conversion supplies the protected control. BH 20000 and time 50 s are additional non-triggering controls. None supplies flight telemetry or validates the original compiled code.

For AI evaluations, include both faulty and nonfaulty tool responses, unauthorized versus authorized operations, and responses that look plausible but do not complete the task. Have someone other than the test generator validate the oracle before evaluating unknown cases.

### 3. Remove one prerequisite at a time, then cross them

Use the [generated prerequisite controls](../results/summary.md#detection-prerequisites-controlled-removals) as a template:

| Obligation | Intervention | Required evidence |
|---|---|---|
| Joint input exposure | Exclude the hazardous input region | Declared support, boundary witnesses, and any dependent input constraints |
| Reachable lifecycle | Deliver it only after the vulnerable phase | Executed path/state trace, including retry and recovery transitions |
| Executable fidelity | Replace real behavior with a nominal mock | A control that fails with the real path and passes with the mock |
| Observability and oracle | Score packet/status presence instead of the contract | Raw output, semantic failure label, and both positive and negative controls |
| Rare-event budget | Reduce n while holding the declared sampling model fixed | Detection-probability calculation and a preregistered target/stopping rule |
| Replay retention | Drop the triggering input or relevant configuration | A regression case that another environment can reproduce, or an explicit evidence gap |
| Response enforcement | Disconnect a retained violation from the release gate | Observable failing exit/status or documented accountable risk disposition |

Keep matched inputs and seeds when comparing harnesses or oracles. Hold unrelated design parameters fixed. Enumerate joint gates when feasible: the lab's 128-row truth table demonstrates how individually plausible steps can fail in combination. Its denominator is not a population sample and must never become a "readiness percentage."

### 4. Choose the budget only after defending exposure

For justified iid per-opportunity detection probability `p`, use `1-(1-p)^n`. If `p=0`, no finite budget helps. If `0<p<1`, no finite random budget guarantees detection. For the lab's invented `p=0.0005`, 5,990 tests meet a 95% target; 10 do not, although either budget could happen to detect a fault. A deterministic boundary witness does not need that random budget.

In an unfamiliar AI deployment, `p` is usually not known. Report that gap, run targeted controls, and use sensitivity analysis over defensible values rather than assuming the toy tail weight. Correlated prompts, shared models, retries, and adaptive generation violate simple iid accounting; a million such interactions are not necessarily a million independent opportunities.

### 5. Make the finding replayable and the response observable

Retain a minimal trigger, phase/state, model/tool/code/configuration versions, oracle version, raw outputs, expected contract, and provenance. Include seeds where relevant, but do not assume a seed reproduces a changing remote model or nondeterministic tool. Store evidence with appropriate access controls; secrets and personal data are not publication artifacts.

Assign a named decision owner, severity, and stopping/escalation rule **before** running the evaluation. Verify that a known failing replay actually produces a failing gate. Verify a protected control is not blocked for the wrong reason. After an intervention, rerun the original witness and unrelated regression controls; a silent error or suppressed diagnostic is not a repair.

The lab's R/A switches model retention and enforcement, not human understanding or institutional follow-through. Its command-line contract demonstrates an exit-code gate. A future evaluation should additionally record time to triage, successful independent replay, disposition, and mitigation quality rather than infer action from an alert count.

### 6. Separate mechanism validation from independent AI discovery

The injected-control protocol answers whether an evaluation pipeline *could expose and preserve a specified failure*. It does not answer whether AI would generate the right input or identify an unknown mechanism without hindsight.

For that empirical question, use the blinded design below with hidden fault catalogs, independent oracle authors, held-out scenarios, matched budgets, and safe cases. Preregister discovery and false-alarm endpoints separately from replay quality and response. Publish unsuccessful attempts and uncertainty. Necessary/sufficient gate equations apply only to their stated dynamic route; they do not rule out static analysis, review, or alternative evidence.

## A 90-minute teaching exercise

1. **0-10 min: prediction.** Present the abstract system without the famous name. Ask participants to state what "a million tests passed" does and does not establish.
2. **10-25 min: assumptions.** Build a register before revealing the overflow. Include phase, conversion, redundancy, and message validity.
3. **25-40 min: falsifiers.** Write boundary and lifecycle tests. Require negative controls for the oracle.
4. **40-55 min: simulation.** Run the notebook. Compare the matched expanded-input runs and explain why three zero-detection results mean different things.
5. **55-70 min: coverage.** Inspect the 256-row grid and the pairwise witness. Identify the higher-order conjunction; explain why the historical fixed design needs fewer varying inputs.
6. **70-80 min: intervention.** Compare removal, conversion protection, isolation, and diagnostic rejection. Identify which property each protects and which it does not.
7. **80-90 min: transfer.** Choose an AI/tool workflow or ordinary software service. Use the prerequisite controls to write a falsifier, lifecycle obligation, oracle, justified budget or explicit unknown, replay record, and response gate.

Score participants on causal understanding, assumption quality, oracle validity, and acknowledgment of uncertainty. Do not score merely on the number of generated tests.

## A future blinded human/AI comparison

The historical case is contaminated by widespread publication. To test "AI would discover this":

- Create unseen domain variants and independently validate their fault/ground-truth catalog.
- Include safe cases, different bugs, distribution shifts, and bugs absent from simplified models.
- Separate test designers from oracle/fault authors.
- Randomize conditions and enforce comparable time/tool budgets.
- Freeze versions and preregister detection, false-positive, time-to-detection and mitigation-quality metrics.
- Report uncertainty with scenario/evaluator clustering and distinguish discovery from recognition.
- Publish every unsuccessful attempt and stopping rule, not just a successful anecdote.

Until that experiment is run, do not assign a percentage to AI's chance of independent discovery.
