# Mariupol: does the model establish when evacuation would have been better?

**Reviewed:** 4 October 2026.

**Scope:** the public Mariupol site, research report, methodology, sensitivity script, repository review documents, and the code producing severity and feasibility conclusions. This is a retrospective evidence and methods review, not operational evacuation advice or a judgment about the researcher.

**Version reviewed:** [`47af9d5decd9502a1084cc5958c0ee5b0e175e05`](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/tree/47af9d5decd9502a1084cc5958c0ee5b0e175e05), committed 26 July 2026. The external project was not modified.

## Bottom line

**Research and methods do exist. They do not establish that evacuation three months earlier was feasible, optimal, or would have produced better outcomes.**

I did not find the specific "three months earlier" claim in the reviewed materials. The current README makes a narrower claim: modelled severity reached its High band in the second week of March, before the UN/ICRC Azovstal operation beginning on 30 April. It explicitly treats the explanation for that delay as a hypothesis rather than an established causal conclusion.

That distinction matters:

| Question | What the reviewed project supports |
|---|---|
| Is there a research report and explicit arithmetic? | **Yes.** The report, methodology and executable sensitivity script are substantial and openly inspectable. |
| Does its default score flag elevated danger before the late-April Azovstal operation? | **Yes, conditionally.** The reviewed code first reaches High on **10 March**, 51 days before 30 April. |
| Does it establish a three-month lead time? | **No.** That claim was not located; its 77-day scoring window runs from 5 March to 20 May. |
| Is the precise timing robust to its own tested choices? | **Not universally.** With exponent 2 and otherwise default settings, the score never reaches High. |
| Does an earlier threshold crossing establish a safe or better evacuation date? | **No.** That requires comparative outcome evidence, feasible options, and contemporaneous information the score does not model. |
| Does the current UI consistently preserve those limitations? | **No.** A generated conclusion still says consent, rather than information or logistics, was the constraint. This is stronger than the revised report supports. |

The strongest defensible reading is **a transparent retrospective illustration of need for protection and the gap to one specific negotiated operation**, not a validated recommendation for when an entire city should have evacuated.

## 1. What research is actually present?

The repository contains:

- [A plain-language research report](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/Mariupol-Severity-Model-Paper.md), including limitations, worked examples, and sensitivity discussion.
- [A methodology document](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/docs/METHODOLOGY.md) specifying components, aggregation, phase cutoffs and feasibility approximations.
- [An executable sensitivity analysis](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/docs/sensitivity.js).
- Public review documents, including a [22 July 2026 review recommending major revisions](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/PEER-REVIEW.md). Their presence is not independent verification of a journal review process or the reviewer's identity.
- A second, spatial feasibility demonstration with building damage, illustrative demographic allocation, nighttime-light proxies and grid-based pathfinding.

The work is not devoid of methods. Indeed, many limitations are explicitly acknowledged. The issue is whether the headline or interface implies a conclusion stronger than those methods can support.

## 2. What the severity model computes

Six quantities are normalized to [0, 1]:

1. Hostility intensity.
2. Kinetic proximity.
3. Protection risk, including corridor violations and consent/filtration categories.
4. Cold burden.
5. Time under siege.
6. Infrastructure damage.

They are combined using a power mean:

`S = ((I^p + P^p + R^p + C^p + D^p + H^p) / 6)^(1/p)`, with default `p = 6`.

At default presentation thresholds, **High** begins at `S >= 0.55` and **Critical** at `S >= 0.70`. The methodology expressly calls these model conventions pending expert-elicitation validation. Calling a band "evacuation warranted" does not independently validate that cutoff as a decision rule or a legal finding.

Input quality is mixed rather than uniformly observed daily data:

- ACLED-derived values are held constant over phases, with later values extrapolated.
- The current implementation contains daily ERA5 reanalysis temperatures. Some surrounding site descriptions still refer to an interpolated climatology.
- Damage is interpolated between anchors; the methodology acknowledges differing spatial areas and, for one anchor, a different measurement unit.
- District population and vulnerability allocations are illustrative estimates.
- Deprivation is partly a clock chosen to saturate after a specified number of days.

This may support a useful teaching index. It does not by itself produce a calibrated probability of death, injury, successful passage, or harm prevented by evacuation.

## 3. I ran the published calculation

The audit fetches the immutable upstream script, checks its SHA-256, runs it in a restricted execution context, and extends its output with first crossings of both relevant thresholds. It does not run route planning or generate new evacuation recommendations.

Reproduce from this study:

```powershell
node tools\audit_mariupol.mjs
node tools\audit_mariupol.mjs --check
```

An internet connection is required to retrieve the pinned source. The original script is linked, not redistributed. The audit runner is for this reviewed source, not a general-purpose sandbox for untrusted programs.

[Machine-readable audit](../data/mariupol-audit.json) records the source revision, hash, original console output and computed comparisons.

| Settings | First High, S >= 0.55 | First Critical, S >= 0.70 | High-or-worse days out of 77 |
|---|---|---|---:|
| Published defaults | **10 March** | **28 April** | 43 |
| Intensity ceiling 4.8 instead of 10 | 5 March | 10 March | 49 |
| Deprivation ceiling 45 instead of 60 days | 10 March | 14 April | 55 |
| Deprivation ceiling 90 days | 10 March | Never in window | 21 |
| Exponent 2 instead of 6 | **Never in window** | Never in window | 0 |
| Exponent 4 | 10 March | Never in window | 34 |
| Intensity 4.8, deprivation 90, exponent 2 | 10 March | Never in window | 6 |

These are deterministic model outputs, **not observed health outcomes or probabilities**. The tested variants come from the project's own sensitivity choices; they do not exhaust all reasonable specifications.

### Three consequential discrepancies

**A. The report's exact baseline date does not reproduce.** Sections 11.10 and 12.3 state 9 March. The current script produces **10 March**. Its 9 March score is below 0.55. This one-day difference does not erase the broad March-versus-late-April gap, but a date-specific conclusion must match the executable evidence.

**B. The report's robustness wording is too broad.** Section 11.10 says the timing survives every tested variant, referring to crossings of lower bands. But at default bounds with `p = 2`, **High is never reached**. A Serious-band crossing at 0.40 is not the same as the project's "evacuation warranted" threshold of 0.55. The defensible statement must specify which threshold is stable and under which choices.

**C. Some reported sensitivity counts are stale.** The report's default table says zero violence-dominant days and mean severity 0.581. The current script returns **2/77** and **0.583**. Its combined low-exponent variant returns **18/77**, not the report's 20/77. The report already recognizes that dominance depends on normalization choices, but its numerical table needs regeneration.

A first crossing also does not mean the score remains above the cutoff thereafter: the default model is High or worse on 43 of 77 days. A robust decision protocol would specify persistence, hysteresis, and consequences of false alarms rather than interpreting the first crossing alone.

## 4. What is wrong with "three months earlier"?

The reference date must first be specified. Three months before the late-April operation, or before the May siege endpoint, falls outside the model's March-to-May scoring window. A three-month lead relative to some other event would require naming that event and tracing its evidence.

The default computed gap is **51 days from 10 March to 30 April**, about 7.3 weeks. That is neither three months nor a demonstrated optimal lead time.

Absence of the phrase in these materials does not prove Christine never said it elsewhere. It means this review cannot attribute that exact proposition to the published project or validate it from the available model.

## 5. Need, feasible passage and best timing are different claims

An earlier high danger score is a statement about the modeled cost of **remaining**. A decision about departure must also consider:

- What would happen while traveling and at the destination.
- Which groups could voluntarily leave and which could not.
- Whether transport, fuel, medical support, receiving capacity, access and credible guarantees existed.
- What was known at the time, rather than reconstructed later.
- The harms of false alarms, failed departure, coercion or family separation.
- How each alternative would affect outcomes compared with remaining or sheltering.

The reviewed work does not estimate these counterfactual outcomes. It does not contain a validated objective function optimizing an evacuation date across alternatives. Numerical severity cannot identify the sole cause of delay, establish a legal obligation by itself, or prove that earlier movement would have been safer for everyone.

The feasibility demonstration is valuable as a conceptual extension, but its [own limitations](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/docs/METHODOLOGY.md#f6-route-computation-dijkstra-pathfinding) say its grid, weights and thresholds are not validated against actual road conditions or movement patterns. It excludes rubble, unexploded ordnance and active fighting along routes.

More specifically, [the implementation](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/teresa.html#L548) assigns an extra finite cost to cells labelled impassable rather than removing them from the graph. A least-cost path can therefore traverse those cells. Its existence cannot establish safe or even physically possible passage.

The [unified UI conclusion](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/index.html#L167) still treats modeled routes as actionable in the organized window and states, in other windows, that the constraint was consent rather than information or logistics. That is inconsistent with the more careful [report section 14.2](https://github.com/Ethical-Tech-CoLab/mariupol-evacuation-model/blob/47af9d5decd9502a1084cc5958c0ee5b0e175e05/Mariupol-Severity-Model-Paper.md#L1055), which explicitly retracts that inference from the arithmetic alone.

## 6. Independent historical checks

Primary ICRC statements support the importance of both agreement and conditions on the ground, but not a precise best evacuation date:

- **6 March 2022:** the ICRC described two failed attempts, an estimated 200,000 intended evacuees, resumed hostilities, and the need for specific agreements and satisfactory security guarantees. The humanitarian need and attempts to act were already recognized; the model is not evidence that nobody knew until an algorithm found the signal. [ICRC statement](https://ir.icrc.org/en/2022/03/ukraine-safe-passage-for-civilians-from-mariupol-halted-for-a-second-day-icrc-calls-on-parties-to-agree-to-specific-terms/)
- **6 April 2022:** the ICRC reported accompanying more than 1,000 people to Zaporizhzhia after they had fled Mariupol themselves. Its team could not enter the city because of security conditions. This was not the later Azovstal extraction, but it rules out casually treating late April as the first humanitarian-assisted movement of any kind. [ICRC statement](https://www.icrc.org/en/document/ukraine-icrc-facilitates-safe-transport-more-500-civilians-zaporizhzhia)
- **Early May 2022:** the ICRC described the Azovstal operation and the specific timing, locations, route, logistical details and voluntary participation agreed by the parties. It also reported facilitating dialogue since late February. [ICRC statement](https://www.icrc.org/en/document/ukraine-civilians-leave-azovstal-safe-passage-operation)

These records explain why the comparison must say **which population, which operation and which outcome**. They do not prove consent was the only limiting factor, nor supply the missing counterfactual that a citywide evacuation months earlier would have succeeded.

## 7. What would have to be true to support the stronger hypothesis?

Reframe it prospectively and precisely:

> For a specified civilian population, a defined voluntary evacuation policy initiated at date t would have reduced expected serious harm relative to the feasible alternatives, using information available at t.

Testing that hypothesis needs more than an extra Monte Carlo run:

| Requirement | Evidence or experiment |
|---|---|
| Defined claim | Specify population, reference event, lead time, alternatives and outcomes; do not equate a score cutoff with optimality. |
| Contemporaneous information | Create an as-of ledger with observation date, publication date, geographic scope, uncertainty and revision history. |
| No future information leakage | Re-run rolling decision dates using only records available then. Historical phase averages extending beyond the decision day and later reanalysis/imagery cannot silently stand in for real-time observations. |
| Calibrated need and decision thresholds | Independent expert elicitation and validation against protection outcomes; assess inter-rater uncertainty rather than borrowing labels from another index. |
| Feasible, voluntary alternatives | Historical evidence of access, enforceable guarantees, transport, receiving capacity and protection risks; independent humanitarian review. |
| Comparative outcome model | Separate need from predicted harms of staying, traveling and arrival. Address selection bias: people able to leave are not a random sample of those remaining. |
| Robustness | Jointly vary weights, cutoffs, exponent, reporting delays and missingness. Report a distribution of recommended dates and conditions under which no recommendation is justified. |
| External validation | Hold out other periods or cases, evaluate false alarms and missed opportunities, and do not fit and validate on the same known outcome. |
| Actionability and governance | Distinguish an alert to seek expert review from an instruction to move. Protect sensitive location and movement information. |

The exact earlier date is **not identified** by the reviewed evidence. That is a research gap, not an invitation to simulate invented movement conditions and present them as validated advice.

## 8. Lessons for AI evaluation and the Ariane hypothesis

Both projects illustrate a boundary between computing the specified quantity correctly and establishing that it answers the real question.

- Ariane: a nominal simulator can omit the faulty implementation.
- Mariupol: a severity score can omit the comparative risks that make a timing recommendation meaningful.
- Both: changing the oracle can make an attractive dashboard certify the wrong claim.
- Both: retrospective knowledge can make a case appear easier to detect than it was prospectively.

For future AI systems, the evaluation should explicitly test whether the system refuses to promote a **proxy** into a **causal or prescriptive conclusion** without the missing evidence. Useful negative controls include a high-severity scenario with unknown feasibility, a path through prohibited cells, a threshold date that disappears under a justified parameter change, and a feature not yet observable at the proposed decision time.

An appropriate AI output in these cases is a bounded conclusion with uncertainty and escalation to qualified review, not a confident date.

## Recommended next revisions to the external project

1. Generate the report's dates and sensitivity tables directly from the current implementation.
2. Carry the report's causal limitations into every UI conclusion.
3. Keep "High", "Critical", earliest crossing and best action date distinct.
4. Treat modeled paths as illustrations until independently validated; distinguish high-cost cells from truly prohibited cells.
5. Publish a dated evidence ledger and evaluate prospective, not hindsight-informed, decision rules.

These are recommendations only. No changes were made to Christine's repository.
