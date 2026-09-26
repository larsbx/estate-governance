# Estate repository template v1

Status: reusable estate architecture contract. Canonical source: `larsbx/estate-governance`.

## Purpose

The template gives every repository in the estate the same answer to four questions:

1. what is authoritative;
2. what mathematical or product domain owns an artifact;
3. which language implements that role; and
4. whether an artifact is canonical, supporting evidence, experimental, generated, or vendored.

The ordering is **authority first, domain second, language third**. A language name
must never be the top-level reason an artifact is trusted.

Each adopter has one root `estate.toml`. That file is the machine-readable source
for repository identity, authority planes, target paths, current transitional paths,
language roles, and migration state.

## Standard planes

Only applicable planes are created. Empty silos are forbidden.

| Plane | Default target | Meaning |
| --- | --- | --- |
| policy | `policy/` | governance, repository authority, backend and acceptance policy |
| kernel | `kernel/` | canonical executable validation owned by the repository |
| proof | `proof/` | theorem/claim state, formal proof packages, proof records and models |
| reference | `reference/` | independently executable semantics and golden-vector generation |
| oracles | `oracles/` | non-authoritative differential checking and research engines |
| experiments | `experiments/` | disposable spikes with explicit promotion/deletion criteria |
| schemas | `schemas/` | versioned boundary and serialization contracts |
| conformance | `conformance/` | accepted, rejected, malformed and boundary vectors |
| vendor | `vendor/` | pinned external code; never visually indistinguishable from local ownership |
| tools | `tools/` | audits, generators and repository maintenance only |
| docs | `docs/` | exposition, research notes, handoffs and audits |
| paper | `paper/` | publication artifacts |
| examples | `examples/` | worked examples that are not proof authority |

A repository may omit irrelevant planes. It may add domain-specific planes only when
their authority is explicit in `estate.toml`.

## Canonical skeleton

```text
repository/
├── estate.toml
├── ARCHITECTURE.md
├── policy/
├── kernel/
│   └── <domain>/
│       └── <language only where useful>
├── proof/
│   └── <claim-or-domain>/
├── reference/
├── oracles/
├── experiments/
├── schemas/
├── conformance/
├── vendor/
├── tools/
├── docs/
│   ├── architecture/
│   ├── mathematics-or-domain/
│   ├── research/
│   ├── handoffs/
│   └── audits/
├── tests/
├── examples/
└── paper/
```

The skeleton is illustrative, not a command to create every directory.

## Authority rules

1. Every acceptance or effect boundary has exactly one canonical implementation.
2. A second implementation is a reference, oracle, formal refinement, generated
   adapter, or conformance checker until an explicit authority migration says otherwise.
3. Cross-language disagreement fails closed.
4. Experiments and oracles never issue acceptance verdicts.
5. Generated surfaces are derived artifacts. Their source must be named.
6. Vendored code is pinned external code and must be distinguishable from locally
   owned source.
7. A computation is not a theorem merely because it is deterministic or exhaustive.
8. Moving a file cannot change mathematical or operational authority.

## Language rule

`estate.toml` records roles, not language prestige. Examples:

```toml
[[language]]
name = "Mojo"
authority = "canonical"
roles = ["kernel"]
acceptance_authority = true

[[language]]
name = "Julia"
authority = "supporting"
roles = ["oracle", "experiment"]
acceptance_authority = false
```

An estate repository may use a completely different language assignment while
retaining the same planes.

## Transitional adoption

Large existing repositories use `layout_status = "transitional"`. Each plane
records its future `target` and the existing `current` paths or `current_globs`.
This permits architecture enforcement before disruptive moves.

Migration order:

1. declare authority without changing it;
2. vendor the template from governance and add the estate audit to CI;
3. separate canonical, reference, oracle, experiment, vendor and generated roles;
4. move one bounded context at a time;
5. update imports and tests in the same PR;
6. delete obsolete compatibility mappings only after CI proves the new boundary.

Mass tree reshuffles are discouraged because they obscure semantic changes.

## Required CI gate

Every adopter runs the estate-layout audit, vendored at
`tools/audit_estate_layout.py`, on every push and pull request. It fails closed on:

- an invalid repository identity or layout status;
- principles other than authority-first ordering, forbidden empty silos, and
  fail-closed cross-language disagreement;
- duplicate plane identifiers or target paths, unknown plane authorities;
- a required plane without a current mapping, or a mapping that resolves to nothing;
- a missing `kernel` or `policy` plane;
- anything other than exactly one canonical language, which must own the kernel role;
- a supporting language holding acceptance authority;
- missing architecture entrypoints (`ARCHITECTURE.md` and this contract);
- a missing, incomplete, or mismatching `[governance]` pin (below);
- a pixi workspace or connected polyglot manifest naming a different repository,
  or a polyglot manifest that does not link to `estate.toml`.

## Governance and vendoring

The canonical contract, manifest template, and audit live in
`larsbx/estate-governance`:

```text
policy/estate.template.toml                          manifest template
kernel/audit_estate_layout.py                        the audit (canonical)
tools/vendor_estate.py                               vendor + pin into a consumer
docs/architecture/estate-repository-template-v1.md   this contract
```

Consumers never import governance at run time. The vendoring tool copies the
audit and this contract byte-for-byte into the consumer and appends a pin to the
consumer's `estate.toml`:

```toml
[governance]
repository = "larsbx/estate-governance"
revision = "<40-hex governance commit>"

[governance.sha256]
"docs/architecture/estate-repository-template-v1.md" = "<sha256>"
"tools/audit_estate_layout.py" = "<sha256>"
```

The audit recomputes both digests, so a local edit of a vendored copy fails CI.
Template changes land in governance first and reach consumers only by
re-vendoring, which is an explicit, reviewable pin bump.

## Adopters

| Repository | Layout | Canonical language |
| --- | --- | --- |
| `larsbx/finite-mandelbrot-research` (first adopter) | transitional | Mojo |
| `larsbx/finite-julia-set-research` | transitional | Mojo |
| `larsbx/finite-math-kernels` | transitional | Mojo |
| `larsbx/julia-oracle-lab` | transitional | Julia |
| `larsbx/langlands-lab` | transitional | Python |
| `larsbx/mandelbrot-bulbs-and-ford-circles-research` | transitional | Python |
| `larsbx/estate-governance` (template source; carries no pin) | canonical | Python |
