# DR-0004 — Periodic estatewide contract conformance audits

- **Status:** accepted
- **Date:** 2026-10-22
- **Decides for:** estatewide contract-evidence auditing
- **Supersedes:** none; complements DR-0002

## Question

What should the paired-vector and immutable-provenance acceptance checks developed
in semantic-categorical-oracle PR #41 run against across the estate, and when?

## Decision

Audit every repository that publishes or consumes a normative contract, canonical
artifact, or verification result. Discover members through
`policy/estate-registry.toml`, then inventory their domain contracts and consumer
relationships. Membership alone does not establish conformance coverage: report
missing contract inventories, unregistered relevant repositories, and inaccessible
sources as coverage gaps rather than successful checks.

| Scope | Required evidence checks |
| --- | --- |
| Domain contract owners | Contract identity/version, schema, domain-owned canonical input/output pairs, immutable revision and path/blob provenance |
| Implementations and ports | Byte-for-byte expected output conformance, deterministic ordering, domain-defined duplicate/conflict handling, and invalid-input refusal |
| Cross-repository consumers | Pins resolve to the recorded paths and blobs; upstream contract changes require deliberate revalidation |
| Approval registries | Pending contracts cannot activate authority; approval requires the applicable version and successful conformance evidence |
| Proof and certificate consumers | Representation conformance cannot grant mathematical proof, certificate acceptance, effect authorization, or persisted-state authority |

Apply domain-specific vectors and rules. The proof-graph provenance ordering rule
is specific to proof graphs; it must not become a universal estate ordering rule.
Initial inventory targets include the relevant FMK, semantic-categorical-oracle,
Senad+/Halaqa, Keel, deontic-circuit, and research-certificate boundaries. This list
is a starting scope, not a claim that all are registered or have runnable checks.

### Triggers

- Every pull request: validate changed contracts and affected consumers.
- Weekly: audit the full discovered estate, including private members through
  authenticated read access.
- On an upstream contract change: promptly rerun affected consumers.

### Reproducibility and freshness

Report these separately:

- **Reproducibility:** the immutable pin resolves to the claimed source paths and
  blobs, and implementations reproduce domain-owned expected output bytes.
- **Freshness:** compare the pinned contract/version to its upstream approved
  contract and report whether review or revalidation is needed.

An older immutable pin may remain reproducible while behind upstream. An upstream
PR head is not an approved domain revision merely because its tests pass. Never
silently re-pin a consumer, update expected outputs, approve a pending contract,
or promote a result based on a scheduled audit.

Each report must identify repository and contract, pinned revision/version,
implementation revision, vector provenance, executed checks and their outcomes,
coverage gaps, and separate reproducibility/freshness findings. Missing credentials,
unavailable runners, and checks not executed are blockers or unverified evidence,
not passes. Findings must identify the affected owner/consumer boundary without
turning an advisory report into authority to act.

## Consequences

- Domain owners retain semantic definitions and canonical expected vectors.
- Consumers retain their named acceptance boundaries under DR-0002. Representation
  normalization alone grants none of the excluded authorities above; a separate
  domain acceptance implementation and its evidence remain necessary.
- Contract changes require reviewed pin updates and conformance validation.
- Operator-controlled scans and PR review enforce publication discipline; holders
  of write tokens can bypass those controls. This policy does not claim otherwise.

## How this is enforced

This decision records the required scope and cadence. It does not install a
scheduler, estatewide dispatcher, contract inventory, approval ledger, or new
runtime authority. Repository acceptance checks and PR review enforce the portions
already implemented; estatewide orchestration remains an engineering follow-up.

Private-repository acquisition must use scoped authenticated read access. The
protected registry-source-read App environment was reported unconfigured on
2026-10-22; estate-governance PR #16 remains blocked on that prerequisite. This
record neither resolves that blocker nor treats anonymous partial coverage as a
full-estate success.

Implementation completion requires an inventory/consumer map, PR and upstream-change
routing, a weekly authenticated runner, durable reports, and negative tests for
wrong vector pins, rule disagreement, missing sources, and attempted promotion.

## References

- [semantic-categorical-oracle PR #41](https://github.com/larsbx/semantic-categorical-oracle/pull/41)
- [finite-math-kernels PR #77](https://github.com/larsbx/finite-math-kernels/pull/77)
- [estate-governance PR #16](https://github.com/larsbx/estate-governance/pull/16)
- Owner instruction, 2026-10-22: record the proposed estatewide scope and cadence,
  open a PR against main, and merge it.
