# DR-0003 — finite-dynamics is archived, superseded by my-math-homelab

- **Status:** accepted
- **Date:** 2026-10-21
- **Decides for:** `larsbx/finite-dynamics`, `larsbx/my-math-homelab`, the estate registry
- **Supersedes:** DR-0001 for `larsbx/finite-dynamics` only

## Question

The 2026-10-09 consolidation (`my-math-homelab` `docs/migration/consolidation-2026-10-09.md`)
superseded the four-program `finite-dynamics` pilot and kept its claim namespaces
FM, FJ, BFC and JO in `my-math-homelab`. Both manifests still declare those
namespaces, so the estate registry, once derived from the manifests, fails its
claim-namespace uniqueness check. Which repository owns the namespaces?

## Prior art

| Source | What it establishes | Transfers? |
| ------ | ------------------- | ---------- |
| `my-math-homelab` consolidation record, 2026-10-09 | `finite-dynamics` superseded, not nested; pilot namespaces kept | yes |
| `kernel/audit_estate_registry.py` | claim namespaces, exports and INV prefixes are estate-unique | yes, for active members |
| SPEC_estate stages | `archived` is a terminal stage | yes |

## Options considered

| Option | What it costs | Why not chosen |
| ------ | ------------- | -------------- |
| **Archive `finite-dynamics`** | one stage change; the audit must release an archived member's names | chosen |
| Remove it from the registry | the estate keeps no record of the pilot's position | loses provenance |
| Rename homelab's four namespaces | contradicts the 2026-10-09 decision; touches homelab locks and program manifests | reverses an earlier decision |

## Decision

`larsbx/finite-dynamics` is at stage `archived` and names this record in
`origin.decision`. `larsbx/my-math-homelab` owns claim namespaces FM, FJ, BFC and JO.
An archived member stays in the registry and the dependency graph but releases its
claim namespaces, exports and INV prefixes.

## Consequences

- **Now obligatory:** new work on the four programs lands in `my-math-homelab`.
- **Now prohibited:** reusing an archived member's names without the active owner's record.
- **Left open:** archiving the GitHub repository itself (owner's setting); the source repositories keep their own authority.

## How this is enforced

`kernel/audit_estate_registry.py` skips archived members in the namespace, export and
INV uniqueness checks and requires every `stated` member to name an accepted decision
record. `tools/snapshot_registry.py --check` fails when the registry drifts from the
manifests. Tests: `tests/test_snapshot_registry.py`.

## Retraction note
