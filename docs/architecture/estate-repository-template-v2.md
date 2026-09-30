# Estate repository template v2

Status: reusable estate architecture contract. Canonical source: `larsbx/estate-governance`.
Supersedes: `estate-repository-template-v1.md`.

v2 carries the SPEC_estate v0.1 manifest (§3) in `ESTATE.toml` and replaces
vendoring with a pinned checkout (§5). This template is the in-repository layout
layer beneath SPEC_estate: SPEC_estate says what exists as a repository and what
may depend on what; this template says how one repository lays out its authority.

## Purpose

The template gives every repository in the estate the same answer to four questions:

1. what is authoritative;
2. what mathematical or product domain owns an artifact;
3. which language implements that role; and
4. whether an artifact is canonical, supporting evidence, experimental, generated, or vendored.

The ordering is **authority first, domain second, language third**. A language name
must never be the top-level reason an artifact is trusted.

Each adopter has one root `ESTATE.toml`. It is the only manifest estate CI reads
from a repository: identity and estate position (SPEC_estate v0.1 §3), then this
template's layout (authority planes, target paths, current transitional paths,
language roles, migration state).

## Repository shapes

The default is one program per repository. Consolidated research repositories may
opt into `[workspace] mode = "multi_program"` and declare directory-rooted programs
and shared components. The additive contract is
[`multi-program-repository-v1.md`](multi-program-repository-v1.md). Permanent
branches are not accepted as program boundaries.

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
their authority is explicit in `ESTATE.toml`.

## Canonical skeleton

```text
repository/
├── ESTATE.toml
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
   owned source. SPEC_estate §5 forbids new vendoring; existing vendored packages are
   declared as a `[[dep]]` whose pin is the digest of the vendored files.
7. A computation is not a theorem merely because it is deterministic or exhaustive.
8. Moving a file cannot change mathematical or operational authority.

## Language rule

`ESTATE.toml` records roles, not language prestige. Examples:

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

## The manifest

```toml
version = 2
template = "estate-repository-v2"

[repo]                        # SPEC_estate §1, §3
id     = "finite-math-kernels"
slug   = "larsbx/finite-math-kernels"
class  = "kernel"             # kernel | substrate | platform | app | research | corpus
layer  = 0                    # the class default unless repo.override names a DR
band   = "HARDENED"           # EXPLORE | STANDARD | HARDENED | LAW; class default unless overridden
stage  = "candidate"          # written by estate CI only
inv    = []                   # INV families this repo owns
default_branch = "main"

[origin]
decided_by = "proposed"       # stated | proposed; proposed caps the stage at candidate
chats      = []               # source chat links, when the repo was crystallized from chats
artifacts  = []               # { path, h = "sha256:..." }

[[dep]]                       # code edge
id  = "estate-governance"
rev = "<40-hex commit>"
pin = "sha256:<digest of kernel/audit_estate_layout.py at rev>"

[[conform]]                   # conformance edge
id      = "julia-oracle-lab"
vectors = "..."

[exports]
names = ["finite_exact", "..."]

[layout]
status = "canonical"          # transitional | canonical

[principles]                  # then [[plane]], [[language]], [migration] as in v1
```

## Required CI gate

Every adopter retrieves the audit as a public, immutable, content-addressed artifact
mirrored from this private governance repository. The workflow downloads the artifact
from a public estate repository at a fixed commit, verifies its SHA-256 against
`ESTATE.toml`, and only then executes it. No credential is exposed to PR-controlled
code, and fork and Dependabot pull requests use the same fail-closed path.

```yaml
- name: Estate audit (pinned public artifact)
  run: |
    set -eu
    rev=$(python3 -c 'import tomllib; print(next(d["rev"] for d in tomllib.load(open("ESTATE.toml", "rb"))["dep"] if d["id"] == "estate-governance"))')
    pin=$(python3 -c 'import tomllib; print(next(d["pin"] for d in tomllib.load(open("ESTATE.toml", "rb"))["dep"] if d["id"] == "estate-governance"))')
    test "$rev" = "<governance-commit>"
    curl --fail --location --proto '=https' --tlsv1.2 --output /tmp/estate-audit.py \
      "https://raw.githubusercontent.com/larsbx/finite-math-kernels/<artifact-commit>/policy/estate-audits/$rev.py"
    printf '%s  %s\n' "${pin#sha256:}" /tmp/estate-audit.py | sha256sum --check --strict -
    python3 /tmp/estate-audit.py --root .
```

The audit fails closed on:

- identity: `version`, `template`, `repo.id`, a `repo.slug` that names `repo.id`;
- estate position: an unknown class, band or stage; a layer or band other than the
  class default without `repo.override = "DR-nnnn"`; `decided_by = "proposed"` with
  a stage past `candidate`; a malformed INV prefix, genesis suite, chat link or
  origin artifact hash; class `meta` anywhere but the governance repository;
- edges: a pin that is not a content hash or signed tag; a missing
  `estate-governance` dep, or one whose `rev` is not a commit or whose `pin` is not
  the sha256 of the audit actually running; a vendored copy of the audit; packages
  vendored from a repository with no `[[dep]]`, or a dep pin that disagrees with
  the digest of those packages in `vendored.toml`; a conformance edge without
  vectors; duplicate deps or exports;
- layout: principles other than authority-first ordering, forbidden empty silos
  and fail-closed disagreement; duplicate plane ids or targets; unknown plane
  authorities; required planes without a current mapping, or mappings that resolve
  to nothing; a missing `kernel` or `policy` plane; anything but exactly one
  canonical language owning the kernel role; a supporting language with acceptance
  authority; a missing `ARCHITECTURE.md`;
- under `layout.status = "canonical"`: a plane not mapped to its target (only
  root-level files beside it), any glob mapping, a pending migration step, or a
  top-level directory that is no plane's target (exempt: hidden directories,
  `__pycache__`, `*.egg-info`, `build`, `dist`, `coverage`);
- a pixi workspace or polyglot manifest naming a different repository, or a
  polyglot manifest that does not link to `ESTATE.toml`.

The audit checks one manifest against one tree. The estate-wide checks that need
every manifest at once (SPEC_estate EA1-EA7: C ∪ D acyclic, layering across
edges, unique exports and INV prefixes, the stage ledger) are not implemented.

## Pinning

```text
policy/ESTATE.template.toml                          manifest template
kernel/audit_estate_layout.py                        the audit (canonical, never vendored)
tools/pin_estate.py                                  set a consumer's rev and pins
docs/architecture/estate-repository-template-v2.md   this contract
```

`tools/pin_estate.py CONSUMER` sets the consumer's `estate-governance` dep to this
checkout's commit and audit digest, and each vendored dep's pin to the digest of
its packages in `vendored.toml`; `--check` reports drift. A template change reaches
a consumer only through that explicit, reviewable pin bump.

## Adopters

Proposed estate positions (`decided_by = "proposed"`, stage `candidate`), until
the owner adopts them by decision record:

| Repository | Class | Layer | Band | Canonical language |
| --- | --- | --- | --- | --- |
| `larsbx/finite-math-kernels` | kernel | L0 | HARDENED | Mojo |
| `larsbx/finite-mandelbrot-research` | research | L3 | EXPLORE | Mojo |
| `larsbx/finite-julia-set-research` | research | L3 | EXPLORE | Mojo |
| `larsbx/julia-oracle-lab` | research | L3 | EXPLORE | Julia |
| `larsbx/langlands-lab` | research | L3 | EXPLORE | Python |
| `larsbx/mandelbrot-bulbs-and-ford-circles-research` | research | L3 | EXPLORE | Python |
| `larsbx/estate-governance` | meta | outside | STANDARD | Python |
