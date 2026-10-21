# DR-0001 — The owner adopts the proposed estate position of every estate repository

- **Status:** accepted
- **Date:** 2026-10-21
- **Decides for:** the estate (all 20 repositories below)
- **Supersedes:** —

## Question

Every estate manifest carried an agent-proposed position (`origin.decided_by =
"proposed"`), which SPEC_estate §3 caps at stage `candidate`. Are these
positions (class, layer, band, canonical language, INV prefixes) the owner's?

## Prior art

| Source | What it establishes | Transfers? |
| ------ | ------------------- | ---------- |
| SPEC_estate v0.1 §1, §3 | class defaults for layer and band; `proposed` caps the stage at `candidate` | yes |
| [`estate-repository-template-v2.md`](../architecture/estate-repository-template-v2.md) | manifest fields, adopter register, the audit | yes |
| `kernel/audit_estate_layout.py` | fails closed on non-default layer/band without `repo.override = "DR-nnnn"` | yes; no override is needed below |
| Estate practice before this record | `finite-dynamics` already `stated`, with no record | superseded by this record |

## Options considered

| Option | What it costs | Why not chosen |
| ------ | ------------- | -------------- |
| Leave every position `proposed` | every repository stays capped at `candidate` with no owner decision on record | positions were reviewed and made uniform with the estate |
| Adopt repository by repository | twenty records for one uniform decision | the positions are uniform; one record states them all |

## Decision

The owner adopts the position below for each repository. Each `ESTATE.toml`
sets `origin.decided_by = "stated"` and names this record. All positions use
their class defaults, so no `repo.override` is required.

| Repository | Class | Layer | Band | Canonical language | INV |
| --- | --- | --- | --- | --- | --- |
| `larsbx/arithmetic-bicycle-conjecture-research` | research | L3 | EXPLORE | Python | `INV-ABC` |
| `larsbx/closure-fiber-of-multiplication-research` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/finite-dynamics` | research | L3 | EXPLORE | Python | — |
| `larsbx/finite-julia-set-research` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/finite-mandelbrot-research` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/finite-math-kernels` | kernel | L0 | HARDENED | Mojo | — |
| `larsbx/giant-fibers-finite-fields-thin-groups` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/julia-oracle-lab` | research | L3 | EXPLORE | Julia | — |
| `larsbx/langlands-lab` | research | L3 | EXPLORE | Python | — |
| `larsbx/mandelbrot-bulbs-and-ford-circles-research` | research | L3 | EXPLORE | Python | — |
| `larsbx/math-vizops` | research | L3 | EXPLORE | Python | — |
| `larsbx/my-math-homelab` | research | L3 | EXPLORE | Python | — |
| `larsbx/novelty-lab` | research | L3 | EXPLORE | Python | — |
| `larsbx/oracles` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/pisot-substitution-conjecture-research` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/pisot-vijayaraghavan-problem-research` | research | L3 | EXPLORE | Python | — |
| `larsbx/s-adic-pisot-conjecture-research` | research | L3 | EXPLORE | Mojo | — |
| `larsbx/tiling-theory-research` | research | L3 | EXPLORE | Python | — |
| `larsbx/vizing-domination-conjecture-research` | research | L3 | EXPLORE | Python | `INV-VDC` |
| `larsbx/estate-governance` | meta | outside | STANDARD | Python | — |

## Consequences

- **Now obligatory:** a change to any adopted position (class, layer, band, canonical language, INV prefix) needs a new or superseding decision record; a non-default layer or band names it in `repo.override`.
- **Now prohibited:** an agent changing an adopted position without a decision record.
- **Left open:** `stage` stays `candidate`. `stated` only lifts the cap; promotion is reserved to estate CI and its stage ledger (SPEC_estate EA1-EA7), which do not exist yet.

## How this is enforced

The audit accepts `stated` and enforces the class defaults and overrides. It
does not check that a named decision record exists or matches. That is a known
gap, and review is the gate until the estate-wide checks exist.

## Retraction note
