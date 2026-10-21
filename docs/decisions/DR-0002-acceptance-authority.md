# DR-0002 — Every estate repository with a kernel holds acceptance authority over a named boundary

- **Status:** accepted
- **Date:** 2026-10-21
- **Decides for:** the estate
- **Supersedes:** —

## Question

The v2 contract let a canonical kernel declare `acceptance_authority = false`
(own no boundary). Should repositories in this estate accept and certify, or
may they sit outside every acceptance boundary?

## Prior art

| Source | What it establishes | Transfers? |
| ------ | ------------------- | ---------- |
| [`estate-repository-template-v2.md`](../architecture/estate-repository-template-v2.md), Language rule | exactly one canonical language; explicit Boolean `acceptance_authority`; boundaries named in `ARCHITECTURE.md` | yes |
| Contract authority rule 7 | a computation is not a theorem merely because it is deterministic or exhaustive | yes: kernel acceptance never yields `proved` |
| `larsbx/vizing-domination-conjecture-research` `ARCHITECTURE.md` | five promotion conditions before its kernel may accept | yes: retained as an exception |

## Options considered

| Option | What it costs | Why not chosen |
| ------ | ------------- | -------------- |
| Flip every repository now | four repositories would claim a boundary no code implements; vizing's guard and conditions would be overridden | declarations must name a real implementation |
| Make it estate law in the audit | removes `false` for code-less adopters and oracle-style repositories | too strict while adopters without kernels exist |
| **Kernels accept now; others when their kernel lands** | four manifests and docs rewritten; five named exceptions | chosen |

## Decision

Every estate repository with a canonical kernel declares `acceptance_authority =
true` and names its boundary and its single implementation in `ARCHITECTURE.md`.
`false` is reserved for:

1. an adopter whose kernel does not exist yet, which switches in the change that lands it: `closure-fiber-of-multiplication-research`, `giant-fibers-finite-fields-thin-groups`, `oracles`, `tiling-theory-research`;
2. a documented, owner-confirmed exception with its own promotion conditions: `vizing-domination-conjecture-research`.

Boundaries adopted on 2026-10-20:

| Repository | Boundary | Implementation |
| --- | --- | --- |
| `arithmetic-bicycle-conjecture-research` | exact certificate acceptance (`computed` only, never `proved`) | `kernel/` |
| `math-vizops` | source acceptance for rendering | `vizops/sources.py` |
| `my-math-homelab` | import acceptance | `kernel/workspace.py` |
| `julia-oracle-lab` | registry admission; oracle results stay evidence | `validate_registry_entry`, `validate_binding` |

## Consequences

- **Now obligatory:** the change that lands a kernel in an excepted repository flips the declaration and names the boundary; vizing flips only when its five conditions are met.
- **Now prohibited:** acceptance verdicts outside a named boundary; kernel acceptance standing in for theorem authority.
- **Left open:** whether the audit should enforce the policy, for example by requiring a named exception for `false`.

## How this is enforced

The audit enforces one canonical language and an explicit Boolean. It does not
enforce this policy or verify boundaries against code. Enforcement is the
contract's non-accepting adopter table, each repository's `ARCHITECTURE.md`,
and review. Vizing's `oracles/replay_row_csp.py` and its test enforce its
exception mechanically.

## Retraction note
