# DR-0005 — Estate governance owns change-impact CI policy

- **Status:** accepted
- **Date:** 2026-11-01
- **Decides for:** location and authority boundary of estate-wide CI selection governance
- **Supersedes:** the placement of the roadmap in `observability-ci-cd`; does not supersede DR-0002 or DR-0004

## Question

Where does policy for selective, dependency-aware CI across the estate belong,
and does selecting tests transfer any acceptance or proof authority?

## Decision

`larsbx/estate-governance` owns the **normative estate-wide policy** for
change-impact planning: versioning, mandatory evidence, missing-source refusal,
cross-repository coverage, and reviewed adoption/pinning. Policy and validators
belong in its existing `policy/`, `kernel/`, and `tests/` planes, with decision
records and architecture descriptions under `docs/`. Do not establish an
independent estate policy authority in `larsbx/observability-ci-cd`.

A consumer repository still owns its executable test suites, authoritative
domain checks, independent oracles, merge acceptance, and CI runners. The
estate-owned planner may report which obligations are affected and whether
coverage is complete. It may not claim that skipped tests passed, silently
replace a required check, change a domain acceptance decision, promote a proof
claim, or authorize deployment. Selection coverage is not mathematical proof.

Policy adoption in consumers is explicit and pinned; the existing estate v2
manifest and its audit remain unchanged by this record. A changed selector or
dependency graph cannot silently invalidate an approved source boundary.
Cross-repository changes require source-specific evidence and owner review.
Inaccessible/private members count as **coverage gaps**, never passes.

## Rollout

The operational design and proposed v1 selector contract are described in
[CI impact governance v1](../architecture/ci-impact-governance-v1.md).
This decision establishes **ownership**; the proposed contract is not yet
a deployed estate-wide executor or a requirement imposed on all adopters.
It does not authorize disabling current CI gates.

Pilot: [SchoolOps PR #28](https://github.com/larsbx/school-ops/pull/28).
Consumer inventory: [Biz-kit issue #245](https://github.com/larsbx/biz-kit/issues/245).
Implementation roadmap: [estate-governance issue #21](https://github.com/larsbx/estate-governance/issues/21).

## Consequences

1. Centralize schema, conformance, receipts, and migration criteria here, not in
   a parallel observability repository.
2. Preserve DR-0002 domain acceptance authority and DR-0004 contract provenance
   and reproducibility/freshness checks.
3. Maintain existing required checks until the source repository has passed
   exact-revision PR and merge-group acceptance and reviewed branch-rule changes.
4. Make failures and exclusions inspectable, with periodic exhaustive comparison.
5. Never infer successful verification from a queued, cancelled, inaccessible, or
   not-executed job.

## How this is enforced

This record fixes ownership and migration discipline by review. No new selector
kernel, consumer pin change, branch-protection setting, or authenticated
estate-wide scheduler is installed by this decision alone. Those are separate
engineering and authorization steps; track them in issue #21.

## Provenance

- Owner instruction, 2026-11-01: place this CI orchestration governance in
  `estate-governance`.
- [Misplaced observability-ci-cd issue #9](https://github.com/larsbx/observability-ci-cd/issues/9)
  was superseded and closed with its history preserved.
