# estate-governance

Canonical repository standards for the larsbx research estate. The current
contract is **estate-repository-v3**: implementation languages are unrestricted,
authority is declared by boundary, and **Lean and Quint formalization are both
required**.

[DR-0006](docs/decisions/DR-0006-language-independent-formalization.md) records the
owner's revised direction. The [v3 contract](docs/architecture/estate-repository-template-v3.md)
defines the manifest, evidence requirements, and migration boundary. Earlier v2
manifests remain historical contracts at their pinned revisions; they do not
become v3 compliant through this change.

## What the standard requires

- Repository identity, explicit authority boundaries, and immutable dependency
  provenance.
- Real Lean proofs and Quint models for declared core obligations, pinned
  toolchains, and a repository-owned formal execution gate.
- A scope document explaining the claims, assumptions, implementation coverage,
  open obligations, and correspondence limits.
- Source-bound execution evidence that distinguishes a successful static audit
  from completed proof and model checks.
- Reviewed consumer adoption. A policy change does not silently change a
  repository's authority, stage, membership, or required CI checks.

There is no prescribed implementation language, canonical-language table, language
role hierarchy, or mandatory empty kernel directory. A repository may use any
combination of implementation languages. Lean and Quint are required verification
technologies, not restrictions on those implementation choices.

## Main surfaces

| Surface | Purpose |
| --- | --- |
| [Manifest template](policy/ESTATE.template.toml) | New v3 repository declarations |
| [Repository contract](docs/architecture/estate-repository-template-v3.md) | Normative v3 requirements |
| [Architecture](ARCHITECTURE.md) | This repository's boundaries and implementation |
| [Formalization scope](docs/formalization.md) | Actual Lean/Quint claims and limits |
| [Layout audit](kernel/audit_estate_layout.py) | Versioned static manifest and source checks |
| [Registry audit](kernel/audit_estate_registry.py) | Recorded estate identity and graph checks |
| [Pinning tool](tools/pin_estate.py) | Exact governance revision and auditor digest |
| [Registry snapshot tool](tools/snapshot_registry.py) | Derive records from exact member manifests |
| [Formal gate](tools/check_formal.py) | Execute the declared formal checks and write evidence |
| [Roadmap](ROADMAP.md) | Remaining engineering and consumer migration work |
| [SchoolOps pilot evidence](docs/audits/schoolops-chrome-install-2026-11-27.md) | Dated Chrome installation, release-verification and CI observations; remaining rollout and G8 obligations |

## Adopting v3

~~~sh
cp policy/ESTATE.template.toml ../CONSUMER/ESTATE.toml
# Fill in identity, boundary declarations, real implementation and formal sources.
# Implement the declared formal gate and wire it into the consumer's CI.
python3 tools/pin_estate.py ../CONSUMER
python3 kernel/audit_estate_layout.py --root ../CONSUMER
~~~

The template is an unfinished starting point. Its example paths must be replaced
with real artifacts. A successful static audit does not establish that Lean or
Quint ran; execute the consumer's formal gate separately and retain its evidence.

Consumer CI retrieves the external governance auditor at the declared commit,
checks its SHA-256, and executes those verified bytes. No auditor is vendored.
The formal gate must execute in CI at the source under review. Existing required
checks remain in place until their migration is explicitly reviewed.

A pin bump does not change the manifest version or supply missing formalization.
Use the same pinning tool with its check option to detect governance drift:

~~~sh
python3 tools/pin_estate.py ../CONSUMER --check
~~~

## This repository's checks

Use Python 3.11+, the pinned Lean toolchain, and the pinned Quint CLI:

~~~sh
python3 kernel/audit_estate_layout.py
python3 kernel/audit_estate_registry.py
python3 tools/render_adopters.py --check
python3 kernel/ci_impact_policy.py --root . --check
python3 -m pytest
python3 tools/check_formal.py
~~~

The formal gate accepts LEAN and QUINT environment variables for the corresponding
executables and writes its default receipt to
formal/evidence/results.json. The default evidence directory is ignored by Git;
a selected final source-bound local receipt may be intentionally committed for
review. CI preserves its own execution receipt as a separate artifact. Its scope is the
abstract evidence state machine documented in [the formalization scope](docs/formalization.md).
It does not prove the complete Python implementation correct.

## Repository shapes and registry history

Single-program repositories remain the default. Durable programs in a shared
repository use directory roots and identity-bound child manifests, as described
in [multi-program contract v2](docs/architecture/multi-program-repository-v2.md).
Program boundaries no longer require a canonical-language declaration.

The committed [estate registry](policy/estate-registry.toml) is an exact historical
snapshot, generated from members' recorded manifests. It is not a claim that every
current repository has migrated or passed formal checks. The generated adopter
table retained in the [legacy v2 contract](docs/architecture/estate-repository-template-v2.md)
describes that snapshot. Do not hand-edit it or relabel legacy rows as v3 evidence.

Mixed-version registry generation is an explicit opt-in through the snapshot
tool's estate-registry-v2 schema and per-contract auditor revisions. Rendering
that new snapshot requires an explicitly selected document. Derived formal
declarations remain unverified until execution evidence is separately checked;
the existing historical snapshot and table are not rewritten by default.

## Related policies

[DR-0004](docs/decisions/DR-0004-periodic-contract-conformance-audits.md) preserves
the distinction between reproducibility, freshness, and inaccessible coverage.
[DR-0005](docs/decisions/DR-0005-ci-impact-policy-ownership.md) places estate-wide
CI selection governance here. Its [validator/planner](kernel/ci_impact_policy.py)
does not execute policy commands or turn skipped tests into passing results.

The [research-literature review protocol](docs/research/periodic-literature-review-protocol.md)
remains advisory. Neither it nor an impact-selection plan confers domain
admission authority.
