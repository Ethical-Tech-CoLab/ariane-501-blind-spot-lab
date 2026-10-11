# Decision-model recommendation: assumption-review support

Date: 2026-10-11. Status: proposed research aid, not a safety mechanism.
Scope: this repository only. Public sources; no live model evaluation.

## Research contract

Reviewed revision `3e0d206576ca7c6b235a9257689de6442ad95432`:
[README](https://github.com/Ethical-Tech-CoLab/ariane-501-blind-spot-lab/blob/3e0d206576ca7c6b235a9257689de6442ad95432/README.md)
and [framework](https://github.com/Ethical-Tech-CoLab/ariane-501-blind-spot-lab/blob/3e0d206576ca7c6b235a9257689de6442ad95432/docs/FRAMEWORK.md).
This is a document/framework assessment, not a full simulator review.

The project emphasizes bounded claims, assumption registers, dependencies,
falsifiers, diverse evidence, oracle quality, test-world fidelity and explicit
uncertainty. More tests or model judgments cannot establish that missing
assumptions or unknown failure modes have been covered.

## Recommended use

After an experiment is recorded, use a bounded semantic assessor to help a
researcher find:

- claims whose cited evidence does not establish the stated scope;
- proposed falsifiers that address a different assumption;
- duplicate or weakly differentiated review items;
- evidence requiring human inspection.

Input: a claim, bounded assumptions, the candidate falsifier and exact source
excerpt. Output: addresses / partially addresses / does not address /
insufficient information. Preserve the source and reviewer decision.

Do not replace numeric overflow checks, simulator execution, failure oracles,
fidelity judgments or the human assertion of research limitations. Do not let
the same model both generate and exclusively certify assumptions.

## Alternatives

First compare a checklist and independent human review. Jev's
[citation support pattern](https://docs.typesafe.ai/cookbooks/citation_check.md)
offers a bounded prototype; Microsoft-Decision-1 and Sage are comparison
candidates, not certified evaluators. A local classifier can be tested if
offline reproducibility matters. Exact proprietary weights are not available
for self-hosting in the researched documentation.

## Test and go/no-go

Have independent reviewers label assumption/falsifier pairs, including
irrelevant-but-plausible tests, unobservable assumptions, circular reasoning,
missing evidence and disagreements. Split by assumption family or scenario.

Measure false reassurance, precision of review alerts, recall of planted
unsupported claims, calibration, disagreement and time per completed review.
Include counterexamples where all simulations pass but the assumption is not
tested. Report that planted-fault performance does not prove unknown-unknown
discovery.

Hard gate: results remain review suggestions; no safety assurance, automatic
test acceptance or certified reliability score. Preserve original experiment
outputs and every limitation. Freeze model/prompt and compare changed versions.

## Economics and pilot

This is added review work, not a demonstrated replacement for expensive LLM
calls. Measure reviewer time and missed issues as well as API cost. Start on
public archived examples, run blind human comparison, and stop if apparent
speed gains increase false reassurance.
