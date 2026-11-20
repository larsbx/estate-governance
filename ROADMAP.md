# Estate governance roadmap

Updated for the owner's 2026-11-20 standards revision.
[DR-0006](docs/decisions/DR-0006-language-independent-formalization.md) replaces
mandatory language-role assignments with explicit boundaries and requires Lean
and Quint formalization. Recorded membership remains in the generated registry;
this roadmap does not assert that every consumer has migrated.

## Current invariants

1. Members are judged under their declared manifest version and exact governance
   pin. A new central contract does not silently update a consumer.
2. Implementation languages are unrestricted. Authority belongs to named
   boundaries, not a language or directory.
3. V3 requires both real Lean and Quint artifacts, scoped obligations, pinned
   toolchains, a CI execution gate, and source-bound evidence.
4. Static audit validity is distinct from completed formal verification.
5. Registry snapshots are generated from exact sources. A historical snapshot is
   not a fresh inventory or evidence of present formal compliance.
6. Membership, stage, authority changes, and required-check migrations remain
   explicit decisions.

## Current implementation

The v3 change supplies the language-independent manifest contract and static
audit rules, templates, scoped Lean/Quint governance artifacts, and a formal
execution gate. Its [scope document](docs/formalization.md) identifies the actual
model claims and correspondence limits. Local and hosted results must be read
from their exact-source receipts and workflow runs, not inferred from this list.

The existing CI impact-policy validator/planner is implemented and remains
read-only. It does not execute selected consumer tests, replace required status
contexts, or establish estate-wide selective execution.

## Formalization and consumer adoption

| ID | Obligation | Completion evidence |
| --- | --- | --- |
| F1 | Adopt v3 in estate-governance itself | Static audit, conformance tests, Lean replay/axiom audit, Quint checks, and source-bound receipt at the reviewed revision |
| F2 | Inventory current consumer manifests and formal artifacts | Exact-source assessment distinguishing v2 legacy, v3 declarations, executed checks, gaps, and inaccessible sources |
| F3 | Migrate Lean-Goose | Real scoped Lean proofs and Quint model/gate, honest implementation correspondence, passing local and applicable hosted evidence, reviewed v3 pin change |
| F4 | Migrate each remaining consumer | Repository-specific boundary declarations, both formal lanes, executable CI gate, actual evidence, and explicit adopted revision |
| F5 | Strengthen implementation correspondence | Named refinements or equivalent evidence connecting each formal scope to actual runtime code; assumptions and uncovered behavior remain visible |
| F6 | Generate mixed-version registry adoption records | Version-aware source derivation, no relabeling of historical declarations as execution success, and reviewed exact-source registry updates |

Lean-Goose's existing native Lean differential checker does not discharge F3's
Lean proof obligation or provide Quint formalization. No consumer migration is
claimed by the central policy revision.

The former G3 goal of enforcing language-linked authority promotion and M1 goal
of automatically flipping non-accepting kernels are **superseded by DR-0006**.
Do not implement those obsolete goals.

## Governance engineering

| ID | Obligation | Completion evidence |
| --- | --- | --- |
| G1 | Authenticated current estate coverage and registry drift checks | A scheduled runner obtains every in-scope source, reports inaccessible members, and detects drift against exact snapshots |
| G2 | Stage-promotion rules and a durable stage ledger | Explicit rules, source-bound ledger entries, and audit enforcement; formal success alone does not promote stage |
| G4 | Review obsolete downstream auditor mirrors | Remove unused copies only in the affected consumer change, preserving provenance and its pinned execution path |
| G5 | Reconcile decision-template identifiers with the DR-nnnn contract | Upstream template correction and reviewed regenerated consumers |
| G6 | Resolve the governance self-snapshot lag | A documented generation policy avoids calling the inevitable predecessor snapshot current without evidence |

These are remaining obligations, not claims of current operational coverage.

## Periodic contract evidence audits

[DR-0004](docs/decisions/DR-0004-periodic-contract-conformance-audits.md) preserves
the periodic audit policy. Remaining work includes current contract/consumer
inventory, PR/upstream-change routing, authenticated scheduled execution, and
durable coverage, reproducibility, and freshness reports. Coordinate with G1.

Historical runner and private-source access problems were recorded in the earlier
roadmap. Recheck their current state during the inventory; do not carry an old
queue state forward as a present result. Missing credentials, inaccessible
repositories, and unassigned runners remain explicit coverage gaps.

## Impact-aware CI

[DR-0005](docs/decisions/DR-0005-ci-impact-policy-ownership.md) keeps estate-wide
selection governance here. The [architecture](docs/architecture/ci-impact-governance-v1.md)
and [issue #21](https://github.com/larsbx/estate-governance/issues/21) track rollout.

| ID | Obligation | Completion evidence |
| --- | --- | --- |
| G7 | Preserve versioned selector validation and fail-closed coverage | Negative tests reject malformed graphs, stale/unknown source identities, and misleading skip claims; formal inputs cannot silently lose coverage |
| G8 | Demonstrate exact-source required gates in the SchoolOps pilot | Relevant PR/merge-group execution succeeds and any protected-context migration is reviewed |
| G9 | Complete Biz-kit interface/dependency coverage | Tenancy, identity, ExtensionV1, Dispatch, and cross-app changes map to accepted source-specific suites |
| G10 | Connect proof/model/certificate dependencies to invalidation | Changes to Lean, Quint, definitions, inputs, generators, or independent oracles invalidate the correct downstream obligations |
| G11 | Compare selected execution with exhaustive authenticated coverage | Durable receipts expose selected, skipped, blocked, and inaccessible checks with missed-coverage measurements |

The [SchoolOps pilot](https://github.com/larsbx/school-ops/pull/28) and
[Biz-kit migration issue](https://github.com/larsbx/biz-kit/issues/245) are consumer
work, not alternate estate policy authorities. Their present state must be
inspected before reporting completion.

## Historical record

The original members adopted v2 through DR-0001, with the former boundary policy
in DR-0002 and finite-dynamics archival decision in DR-0003. The committed registry
retains its recorded identities and stages. Decisions and historical results stay
available; they are not proof of current source freshness or v3 compliance.

Outstanding ownership/archival and proposed-membership questions should be checked
against current repository state and decision records during F2. No archival,
membership change, bulk pin bump, or branch-protection change is performed by this
roadmap revision.
