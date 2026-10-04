# AI usage and human direction

## Disclosure, not a performance claim

This retrospective lab was produced with an **AI assistant using Copilot SDK in VS Code**. AI assistance is part of the provenance of the research, not evidence that AI would independently have discovered the Ariane 501 failure.

The user supplied the research question, hypothesis, reference examples, and publication direction. The assistant performed source discovery and reading, designed the synthetic mechanism experiment, and wrote code, documentation, and tests. A delegated website subagent implemented the static research site, interactive demonstration, website tests, and Pages workflow.

No independent human scientific validation was performed in-session. Human direction and publication decisions are not represented as independent validation.

## What AI did, and what it did not do

| Activity | Disclosure |
|---|---|
| Question and hypothesis | Supplied by the user |
| Research examples and publication direction | Supplied by the user |
| Source discovery and reading | AI-assisted; source-specific access and verification status recorded in the source catalog |
| Synthetic experiment design | AI-assisted and informed by the known historical failure |
| Code, documentation, and tests | AI-generated/AI-assisted; executable checks are not independent scientific review |
| Website and interactive demonstration | Implemented by a delegated website subagent |
| Model training or fine-tuning | None performed |
| Blinded comparison of AI discovery ability | None performed |
| Flight telemetry or recovered flight executable | None obtained or used |
| Independent human scientific validation | None performed in-session |

The historical inquiry and other external publications retain their own authorship. This lab neither claims their endorsement nor implies endorsement by Channi Greenwall, ESA, CNES, or NIST.

## What is not measured

| Quantity | Recorded value | Why |
|---|---|---|
| Verified model identifiers and versions | Unknown | No verified identifiers recorded for publication |
| Total input, output, or cached tokens | Unknown | No reconciled project usage export recorded |
| Request and subagent usage totals | Unknown | No reconciled project usage export recorded |
| Wall-clock, model, or human working time | Unknown | No verified timing totals recorded |
| Monetary cost or list-price equivalent | Unknown | No reconciled billing/usage calculation recorded |
| Energy or carbon footprint | Unknown | No project measurement or justified estimate recorded |

**Unknown is not zero.** No scores, totals, model names, or efficiency claims are inferred from the amount of code or the existence of this site. No ledger was extracted to produce this disclosure, and it is not a generated `usage-calc` dashboard.

## Research tool access

Tavily search and extraction were attempted, but the configured API key was rejected. A secure key update was requested; no replacement was available. Research continued through alternative web search and direct retrieval. No Tavily-assisted findings are claimed.

Direct ESA pages returned HTTP 403. The primary inquiry was read via its University of Minnesota mirror, with independent CNES material for Ariane 4 chronology. The [source catalog and access log](../data/sources.json) distinguish directly read material, metadata-only verification, and unavailable evidence.

## The CoLab disclosure method used here

This page adapts the evidence-first reporting practice documented in:

- [Ethical Tech CoLab: usage-calc](https://github.com/Ethical-Tech-CoLab/usage-calc#readme), which reports requests, tokens, money, model time, human time, and explicit measurement limitations from a usage ledger, rather than guessed totals.
- [Silencing the Span: usage methodology](https://github.com/Ethical-Tech-CoLab/manhattan-bridge-noise-dumbo/blob/main/usage/README.md), the originating worked example, which explains field provenance, attribution, aggregation, and limits.
- [Silencing the Span: published usage dashboard](https://ethical-tech-colab.github.io/manhattan-bridge-noise-dumbo/usage/usage-dashboard.html), a public example of usage transparency alongside a research project.

These sources were inspected on **4 October 2026**. Their numerical results and source-rating scores belong to those projects; none is transferred to this lab. We adopt the distinction between measured, inferred, and unavailable information, not an invented CoLab certification or scoring rubric.

## Website design provenance

The website was informed by the public [Silencing the Span](https://ethical-tech-colab.github.io/manhattan-bridge-noise-dumbo/) and [Agentic Language Development](https://ethical-tech-colab.github.io/agentic-language-development/) sites and their [research-page builder](https://github.com/Ethical-Tech-CoLab/manhattan-bridge-noise-dumbo/blob/main/build_pages.py) and [static site source](https://github.com/Ethical-Tech-CoLab/agentic-language-development/blob/main/index.html). The adopted patterns are a clear editorial entry point, readable full research, explicit evidence boundaries, static delivery, and prominent links to provenance.

Site styling is original, with blue, purple, and amber accents drawn from this lab's existing charts. External texts, graphics, and usage figures are linked rather than copied.
