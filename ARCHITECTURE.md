# Repository architecture

This repository owns the estate standards, their static auditors, and supporting
pinning and registry tools. Its current standard is
[estate-repository-v3](docs/architecture/estate-repository-template-v3.md).

The root [ESTATE.toml](ESTATE.toml) declares this repository's identity, named
authority boundary, actual implementation paths, and required Lean and Quint
formalization. Authority belongs to the declared boundary and contract; no
implementation language has special estate authority.

## Implemented surfaces

| Surface | Path | Role |
| --- | --- | --- |
| Policy | policy/ | Manifest/program templates and recorded estate membership |
| Auditors | kernel/ | Static repository and registry validation; CI impact-policy validation |
| Formalization | formal/ | Lean proofs and Quint models of the scoped evidence contract |
| Conformance | tests/ | Valid baselines and rejecting mutations |
| Tooling | tools/ | Pinning, registry generation, table rendering, and formal execution |
| Documentation | docs/ | Versioned contracts, decisions, formal scope, and migration guidance |

These are this repository's chosen paths, not a mandatory estate skeleton.
Consumers can use their existing structure and implementation languages.

## Governance boundary

The manifest names the estate-contract-validation boundary and its implementation
files. The static auditors check declarations, paths, content identities, and
recorded governance conditions. They do not infer the truth of a domain claim
or prove arbitrary implementation behavior from metadata.

Consumers execute the repository auditor from the exact governance revision and
SHA-256 declared in their own manifest. Historical v2 consumers remain subject
to their declared version. The v3 auditor can interpret legacy contracts without
claiming that those consumers satisfy the new formalization requirements.

Estate-wide state is separate. The registry records exact member snapshots, and
its audit checks the applicable snapshot contract, graph direction, uniqueness,
governance pins, and stage declarations. Reciprocal conformance edges are not
code dependencies. A valid historical registry is not a fresh estate inventory.

## Formalization boundary

The [formalization scope](docs/formalization.md) states the exact obligations.
Lean proves properties of an abstract evidence-transition model: a verified state
requires successful, current evidence from both formal lanes, and evidence
transitions preserve the declared domain authority. Quint checks the corresponding
model through declared tests and bounded exploration, including an unsafe
transition that must yield a counterexample.

The [formal execution gate](tools/check_formal.py) records toolchain identities,
commands, source hashes, execution outcomes, and before/after source identity.
A stale successful receipt is not reusable evidence for changed source.

These checks establish the stated abstract-model results. They do not prove
correspondence between that model and every Python audit, pinning operation,
GitHub behavior, or consumer implementation. No universal theorem is inferred
from bounded Quint execution. Domain admission, deployment authorization, and
mathematical claims outside the declared scope remain separate.

## Layout and programs

V3 removes compulsory language-role tables and the requirement to invent a kernel
or policy plane. An optional plane inventory is validated when present; declaring
a canonical inventory retains the complete-mapping checks described by the
contract. This repository retains an inventory because it usefully describes
existing files.

Multi-program repositories use stable directory roots and child identities under
[multi-program contract v2](docs/architecture/multi-program-repository-v2.md).
Their root manifest owns boundary and formalization declarations. A program's
language choice does not confer authority.

## Change and migration discipline

[DR-0006](docs/decisions/DR-0006-language-independent-formalization.md) supersedes
the former language ownership and automatic kernel-authority promotion rules.
It does not repin consumers, rewrite historical evidence, promote estate stages,
or register new members. Each consumer migration must supply its own real formal
artifacts, exact-source execution evidence, and reviewed pin change.
