# Estate-wide change-impact CI governance v1 (proposed contract)

**Status:** architectural specification. A local read-only v1 schema validator and
selection planner are proposed in the companion implementation PR. They do not
execute suites or establish estate-wide runtime adoption.
**Owner:** `larsbx/estate-governance` under [DR-0005](../decisions/DR-0005-ci-impact-policy-ownership.md).
**Other obligations:** DR-0002 retains domain acceptance authority; DR-0004
retains contract conformance, provenance, and freshness requirements.

## Purpose and authority

The estate policy defines *which verifications must run after a particular
source change*. Consumer repositories retain their test implementations and
acceptance decisions. Repositories may share a pinned selector implementation,
but the policy source, schema, conformance and exception governance live here.
The observability/CI-CD repository is an operational consumer, not an
alternative policy authority.

A selector only offers a justified plan. It cannot establish that a theorem is
proved, a certificate is sound, a contract is approved, or a deployment is safe.
Those verdicts require the applicable domain owner and exact-head evidence.

## Plan and dependency model

Let `R` be the source revision being tested, `B` the verified comparison
base, and `Δ(B,R)` the complete changed-path set. A versioned policy defines:

- Components and explicitly owned file paths; test modules and executable suites.
- Directed dependency edges and ownership of cross-repository contracts.
- Always-run preflight, mandatory acceptance/security checks, and risk classes.
- Conditions requiring full verification: unknown paths, changed policy/selector
  implementation, shared build configuration, unverifiable dependency edges,
  missing baselines, ambiguous renames, and stale/missing source provenance.
- Evidence sources for mathematical generators, proof definitions, parameters,
  certificates, independent exact oracles and committed golden outputs.

If `a -> b` means component `a` depends on `b`, any modification to `b`
invalidates tests/verification obligations for `a`, transitively. This is a
**reverse dependency closure**, not merely a directory glob match.

The plan's required set is:

`always_run ∪ mandatory(Δ) ∪ suites(reverse_dependency_closure(owners(Δ)))`.

Selection is conservative. When a path cannot be mapped *confidently*, run
all applicable suites or block (never mark an unexecuted suite as passed).
An empty change set still executes unconditional governance/preflight checks.

A policy may safely skip a suite only with a declared, inspectable reason,
validated by conformance tests and periodically checked against exhaustive
execution. An incorrect but syntactically valid dependency map is a coverage
risk; an exhaustive run alone does not prove the map complete.

## Suggested versioned artifacts (not yet normative)

A per-consumer policy such as `policy/ci-impact.toml` (or a mechanically
equivalent pinned schema) describes components, dependencies, suites,
acceptance requirements, and full-run triggers. A shared validator must
reject schema drift, cycles, duplicate ownership ambiguity, unknown references,
untrusted commands, empty required suites, and missing test modules.

An immutable JSON result should contain:

```json
{
  "schema": "estate-ci-impact-v1",
  "repository": "larsbx/example",
  "tested_revision": "<full tested SHA>",
  "comparison_base": "<full base SHA>",
  "policy_revision": "<pinned governance SHA>",
  "policy_digest": "sha256:<hex>",
  "changed_paths": [],
  "direct_components": [],
  "dependency_closure": [],
  "selected_suites": [],
  "skipped_suites": [{"suite": "example", "reason": "unaffected under policy rev"}],
  "unmapped_paths": [],
  "source_coverage": "complete",
  "decision": "targeted"
}
```

The sample values are placeholders, **not** a generated acceptance receipt.
An implementation must also bind the execution results, tools, attestations
and artifacts to the precise tested revision. A receipt must distinguish:
`passed`, `failed`, `skipped-with-justification`, `not-run`,
`blocked`, and `inaccessible`.

## CI orchestration and trust rules

1. Trigger a stable required workflow **unconditionally** for PRs and
   `merge_group` when the merge queue is used. Filter selected jobs *inside*
   it. Path-filtered required workflows may remain pending.
2. Keep one constant final gate that checks every selected prerequisite,
   including planner failure, cancellation, skip and runner acquisition.
   Do not treat missing jobs or skipped required dependencies as success.
3. Plan against verified source inputs and test the intended effective merge
   revision. Record the base SHA, head SHA, and tested checkout SHA separately
   when they differ. Fail closed on stale or unavailable ancestry.
4. Keep PR-controlled code unprivileged; do not run it with estate read tokens,
   deploy credentials, protected signing material or approval powers. A protected,
   pinned selector may parse untrusted source/manifest *as data*. Changes to
   policy or CI wiring force independent, conservative validation.
5. Cancel only superseded PR-head attempts. Do not cancel mainline, protected
   merge-queue, release, or evidence-preserving computations as an optimization.
6. Maintain existing branch-protection check names until their replacement
   passed on exact heads and a reviewed ruleset migration is complete.
7. Use content-addressed caches only when the full dependency/toolchain/input
   closure matches; caches must not promote acceptance or hide execution failure.

## Research and proof obligations

For mathematical programs, test selection additionally invalidates the
transitive closure of theorem definitions, exact arithmetic libraries,
certificate generators, oracle code, input seeds/parameters, expected outputs
and proof-bank claims. Preserve domain-specific negative controls and required
independent reproduction. A passing exact computation can justify a
**computed** receipt; it is never automatically **proved**.

For a certificate or imported result, check *reproducibility* against its
immutable pins separately from *freshness* compared with accepted upstream
revisions. A failed acquisition, pending check or missing independent oracle
is incomplete evidence, not accepted verification.

## Estate-wide implementation stages

| Stage | Deliverable | Acceptance |
| --- | --- | --- |
| 0 | Governance ownership and issue/roadmap | DR-0005 recorded, consumer boundaries unchanged |
| 1 | Versioned policy schema, validator, conformance suite | Negative tests for unknown paths, bad edges, policy change, missing modules and test skips |
| 2 | SchoolOps pilot exact-head PR/merge-group evidence | No dangling required statuses; all selected jobs & final gate succeed |
| 3 | Biz-kit dependency and contract inventory | Tenancy, authorization, shared umbrella, ExtensionV1 and Dispatch boundaries explicitly modeled |
| 4 | PSC/tiling proof-aware artifact graph | Correct exact hashes, independent oracles, provenance and downstream invalidation |
| 5 | Estatewide scheduled exhaustive comparison | Authenticated source coverage, reproducibility and freshness reports with explicit gaps |
| 6 | Adopt reviewed pinned consumer policies | Measured CI minutes, tail latency and false-skip counterexamples; conservative rollback |

## Open blockers and non-goals

Registry source authentication and private member coverage remain blocked as
recorded in [DR-0004](../decisions/DR-0004-periodic-contract-conformance-audits.md)
and estate-governance PR #16. GitHub App access did not expose branch protection
in the initial pilot. Neither missing credentials nor unavailable runners justify
relaxing acceptance.

This specification **does not** install a scheduler, selector executable,
policy audit, branch rule, or credential flow. It does not subsume a project's
existing domain-specific acceptance or original CI workflows.

## Tracking

- [Estate-wide CI governance issue #21](https://github.com/larsbx/estate-governance/issues/21)
- [SchoolOps pilot PR #28](https://github.com/larsbx/school-ops/pull/28)
- [Biz-kit migration issue #245](https://github.com/larsbx/biz-kit/issues/245)
