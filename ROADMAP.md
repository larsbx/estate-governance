# Estate governance roadmap

Status: as of 2026-10-22. Machine-readable state lives in `policy/estate-registry.toml`
(generated) and `docs/decisions/`; this file tracks what remains.

## Invariants

1. Every member passes `kernel/audit_estate_layout.py` at the governance revision it pins; a template change reaches a member only through a reviewed pin bump.
2. The registry is generated from members' manifests (`tools/snapshot_registry.py`), never hand-edited.
3. Every `stated` position names an accepted decision record; `proposed` caps the stage at `candidate`.
4. A repository with a kernel holds acceptance authority over a named boundary (DR-0002); the exceptions are listed in the contract.
5. Kernel acceptance never yields `proved`; theorem status stays with proof records.

## Done (2026-10-20 to 2026-10-22)

- All 20 original members adopted `estate-repository-v2`, pinned to `5ea47de`, with CI fetching the audit directly from this repository at the pinned revision.
- Positions adopted by the owner (DR-0001); acceptance-authority policy recorded (DR-0002); `finite-dynamics` archived, superseded by `my-math-homelab` (DR-0003).
- Registry generated from manifests; estate-wide audit checks decision records, the `proposed` cap and archived-name release. `llm-kernel-lab` registered.

## Open

### Owner actions

| ID | Item | Done when |
| --- | --- | --- |
| O1 | GitHub Actions never assigns a runner for the private members (`giant-fibers-finite-fields-thin-groups`, `closure-fiber-of-multiplication-research`, `oracles`): check Settings → Billing → Actions minutes and spending limit. `finite-julia-set-research` (public) has had no runner since 2026-10-20 despite workflows identical to green members: check its Settings → Actions. | every member's estate gate runs green on `main` |
| O2 | Archive the `larsbx/finite-dynamics` GitHub repository (left open by DR-0003). | repository archived on GitHub |
| O3 | `llm-kernel-lab` is `proposed`: adopt or amend its position by decision record. | it names an accepted DR |

### Governance engineering

| ID | Item | Done when |
| --- | --- | --- |
| G1 | Registry drift is checked only locally: `snapshot_registry.py --check` needs sibling checkouts. Add a scheduled workflow that checks out every member (private members need a read token) and runs it. | drift fails a scheduled CI run |
| G2 | No estate CI writes `stage`, and no stage ledger exists; every member stays at `candidate` (or `archived`). | promotion rules and a ledger exist, and the audit verifies them |
| G3 | DR-0002 is not enforced: the layout audit accepts `acceptance_authority = false` without a named exception. Enforcing it changes the pinned audit, so every member needs a pin bump. | audit rejects an unlisted non-accepting kernel, and all members are re-pinned |
| G4 | `finite-math-kernels/policy/estate-audits/` (mirrors for `0833929`, `63b5605`, `f5fe90d`) is no longer read by any gate. | mirror removed in `finite-math-kernels` with its provenance regenerated |
| G5 | The decision template rendered from `larsbx/agent-icm` numbers records `D-NNNN`; the audit uses `DR-nnnn`. | template fixed upstream and re-rendered |
| G6 | The governance row necessarily snapshots the commit before the change that writes it, so `--check` reports it one commit behind after each merge. | snapshot excludes the governance row from drift, or CI regenerates it post-merge |

### Member migrations

| ID | Item | Done when |
| --- | --- | --- |
| M1 | Non-accepting members switch to `acceptance_authority = true`: `closure-fiber-of-multiplication-research`, `giant-fibers-finite-fields-thin-groups`, `oracles` and `tiling-theory-research` when their first kernel lands; `vizing-domination-conjecture-research` when its five promotion conditions are met. | each flips in its kernel-landing change, and the contract's exception table empties |
| M2 | Transitional layouts with pending migration steps: arithmetic-bicycle (4), closure-fiber (4), giant-fibers (4), my-math-homelab (4), novelty-lab (3), math-vizops (2), oracles (2), tiling-theory (2), vizing-domination (2). | each declares `layout.status = "canonical"` with no pending steps |
