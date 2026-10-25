# Periodic literature review for the research estate

- **Status:** advisory research process (not an adopted domain contract or theorem verdict)
- **Document version:** 0.1
- **Recorded:** 2026-10-25
- **Scope:** publicly and accessibly discoverable mathematical/scientific research repositories in the `larsbx` GitHub estate
- **Authority:** project owners and their repository-local approval/proof gates; this note grants no cross-repository write, merge, claim-acceptance, or publication authority

## Purpose

Use periodic primary-literature review to identify relevant results, counterexamples, proof techniques, reproducibility artifacts, and connections across research programs **before changing a project's research plan**. Produce source-backed recommendations tied to an inspected repository revision. Do not replace mathematical review with keyword matching or treat an automated digest as proof.

This **complements, but is different from,** [DR-0004](../decisions/DR-0004-periodic-contract-conformance-audits.md): contract conformance checks code/representation evidence, while literature review assesses prior art, mathematical assumptions, novelty, and potential roadmap changes. Neither audit transfers the acceptance authority held by the owning program.

## Actual scheduling and implementation boundary

An enabled ChatGPT automation entitled **Research Repos Literature Review** was created on 2026-10-25, with a **weekly Friday** recurrence (user timezone: America/New_York, flexible execution window). It asks for an evidence-backed cross-repository literature briefing, compares findings with previous briefings, and makes **recommendations only**. This is a ChatGPT scheduled task, **not** a GitHub Actions workflow, service deployed to servers, or automatic PR creator.

Separate existing dedicated briefs (e.g. Senad+, SecClaim, autonomous research) should not be duplicated: focus this review on cross-repository synthesis, gaps, reusable lemmas, and plan implications. Existing automations and dates should be checked in the scheduling system rather than inferred from this static note.

**Proposed, not installed:** (i) a monthly synthesis of sustained findings, (ii) an operator-reviewed GitHub PR publication flow for accepted digests, and (iii) source-harvesting automation. Do not claim these are operating or schedule meetings without authorization.

## Scope discovery

1. Enumerate research repositories accessible under `larsbx`, then compare against the authoritative [estate registry](../../policy/estate-registry.toml) and [multi-program workspace](https://github.com/larsbx/my-math-homelab). The registry is a snapshot; absence from it does not imply a repository is irrelevant or nonexistent.
2. Give priority to active math/science research programs; include emerging repositories, notably `tensor-multiplication-research`, `finite-math-kernels`, `graph-product-ring-research`, and other active mathematics work when relevant. Do not indiscriminately scan deployment, business-application, or infrastructure repositories.
3. For each selected repository read its current `main` and relevant README, plans, issue/PR status, mathematical claims, referenced proof artifacts, CI evidence, and provenance. Record the exact revision and access gaps. An imported program in `my-math-homelab` may be locked to an older source SHA; use the still-authoritative source repository unless its authority was explicitly transferred.
4. Note dedicated programs with a standing review cadence so the cross-repo review supplements rather than repeats that work.

## Literature retrieval

Search **primary sources**, starting with [arXiv](https://arxiv.org/), journal publishers and DOI records ([Crossref](https://www.crossref.org/)), proceedings, and verified proof/code repositories. Relevant subject groups include `math.RA` (rings and algebras), `math.GR` (group theory), `math.RT` (representation theory), `math.AG` (algebraic geometry), `math.CO` (combinatorics), `math.NT`, `cs.SC` (symbolic computation), and others as dictated by the projects. `math.RT` does **not** mean rational trigonometry. Avoid a single catch-all keyword or blanket exclusion of an adjacent domain.

For each weekly pass prioritize works **newly published or materially revised since the preceding edition**, starting with a seven-day lookback for the initial review. Older foundational references are welcome when they resolve an active proof obligation or novelty concern; label them as background and never pass them off as newly published. Prefer the canonical DOI/arXiv/publisher URL; record title, authors, date, version, and source type. Do not redistribute paywalled or copyrighted PDFs without permission.

A retrieved abstract is not a verified theorem: inspect the full statement, hypotheses and method where possible. Avoid false matches from overlapping terms such as “Cayley”, “tensor”, “representation”, and “octonion”.

## Evidence and triage discipline

Each candidate finding is logged with:

| Field | Required information |
| --- | --- |
| Bibliography | authors, title, venue or archive, publication/update date, DOI/arXiv link and version |
| Reliability | peer reviewed / preprint / thesis / note; proof artifact present or absent; what was actually inspected |
| Mathematical domain | characteristic, field size or finiteness, dimension/rank, algebra laws, guards and exceptions |
| Result | exact theorem/negative result/conjecture, and applicability limits |
| Relevance | affected repository(s), current claim or roadmap item, inspected commit/PR/path |
| Disposition | newly actionable / already accounted for / needs verification / irrelevant, with reason |
| Proposed follow-up | concrete lemma, counterexample, test, literature check, experiment, or roadmap change, with priority |
| Authority | reviewer/owner decision pending; no automatic claim promotion or change to normative text |

Prefer **5–10 high-signal findings** over padding. When nothing material is found, say so. Explicitly identify gaps, failed searches, inaccessible papers, uncertain inferences, and corrections to previous digests.

For work involving finite-field geometry, tensor multiplication, Cayley/Clifford/Jordan structures, Aschbacher classes, or algebraic RT, preserve the distinctions already established in `tensor-multiplication-research`: characteristic restrictions, projective denominator guards, tensor compatibility laws, semilinear covariance versus strict invariance, planar RT versus higher-rank Gram corrections, and a verified proof versus symbolic examples.

## Publication and review interface

**Recommended destination for actual repo-specific findings:** that program's literature folder or research notes, under its own review process. **This document** is the estate-level discovery/triage protocol and belongs here; it is not the primary home of any program's mathematics.

The weekly ChatGPT digest should include a portfolio summary, references, repository-by-repository proposed next steps, and a short list of cross-program reusable insights. Only after a human/repository-authorized review should findings be encoded as an issue or PR in a domain repository. A green CI check does not certify novelty, mathematical proof, or correctness of a cited article.

A proposed monthly report (not currently scheduled by this document) could summarize the most significant developments, accepted/rejected plan changes, unverified claims, and proof gaps. Keep immutable source links and digest dates to support longitudinal comparisons. Resist optimizing for paper counts as a proxy for mathematical progress.

## First implementation gates

- **G0 — Task recorded:** verify that the weekly ChatGPT automation exists and is enabled. This is already recorded above; future reviews should re-check live state when needed.
- **G1 — Inventory:** establish coverage of active accessible research repositories, note missing/locked/out-of-scope entries and source authority.
- **G2 — Evidence quality:** run an initial literature baseline with actual citations and explicit negative results; the initial Deep Research planning memo was **not** a completed evidence-backed literature survey.
- **G3 — Feedback:** compare subsequent digests with previous findings and current source-branch revisions; propose actionable changes without automatically making them.
- **G4 — Optional publication:** only if authorized, implement an independently reviewed workflow to commit a digest and open a PR against the appropriate project; audit it as a separate integration.
- **G5 — Optional monthly synthesis:** add a separate cadence only upon instruction; do not infer a standing meeting or team rota.

## Research baseline and source provenance

This note adapts the 2026-10-25 Deep Research *Periodic literature review scheduling* planning output into a repository protocol. That output primarily proposed sources and workflow ideas and did **not** include an inspected, citation-backed portfolio of newly published papers. It is therefore **not** represented as a literature-review result.

Background process references: [estate-wide contract evidence audit decision](../decisions/DR-0004-periodic-contract-conformance-audits.md), [estate architecture](../../ARCHITECTURE.md), and [tensor-multiplication research plan](https://github.com/larsbx/tensor-multiplication-research/blob/main/research/higher-rank-tensor-program.md).
