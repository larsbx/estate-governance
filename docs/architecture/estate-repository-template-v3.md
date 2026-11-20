# Estate repository template v3

Status: current versioned estate standard, implementing the owner direction in
[DR-0006](../decisions/DR-0006-language-independent-formalization.md).
Canonical source: larsbx/estate-governance.
Supersedes v2 for repositories that explicitly adopt version 3.

V3 removes mandatory implementation-language assignments and adds required
**Lean and Quint formalization**. Authority attaches to declared boundaries and
their implementations. Implementation language, directory name, and formal
toolchain choice are distinct facts.

## Purpose and preserved requirements

Every adopter declares:

1. its identity, estate position, and immutable dependency provenance;
2. its owned acceptance/effect boundaries, or their absence;
3. the existing implementation files and contracts for those boundaries;
4. its Lean and Quint sources, obligations, toolchains, and execution gate; and
5. the scope and limitations of its formal evidence.

The order is **authority, then domain**. Implementation languages are unrestricted.
There is no requirement for one canonical language, a kernel language role,
supporting-language classifications, or a language-specific oracle lane.

The root ESTATE.toml remains the estate manifest. ARCHITECTURE.md remains required.
Identity, class/layer/band rules, explicit origin, dependency hashes, export
uniqueness, and proposed-stage restrictions are retained. Formal verification
does not automatically promote a stage, register a repository, or grant domain
authority.

## Repository authority

~~~toml
[authority]
acceptance_authority = true

[[boundary]]
id = "definition-admission"
implementation = ["src/checker", "src/boundary_adapter"]
contract = "docs/definition-admission.md"
~~~

The Boolean is required. A true declaration requires one or more named boundary
entries. A false declaration requires no accepting boundary entries. Each boundary
has a stable, unique id, a nonempty list of existing repository-relative
implementation files, and an existing repository-relative contract document.

An implementation may contain several components and languages. The contract
must identify the decision or effect, its input/output meaning, and the
implementation that owns it. Independent references, external proof checkers,
and evidence-producing tools do not silently become additional authorities.

A repository with no owned accepting boundary declares:

~~~toml
[authority]
acceptance_authority = false
~~~

It may still implement references, models, proofs, audits, and experiments.
Their results must not be presented as its own domain admission or deployment
authorization. Reporting that Lean checked a named proof preserves Lean's proof
checking boundary; it does not grant the repository a new operational boundary.

Adding a kernel or executable does not automatically flip this Boolean.
Changing authority requires an explicit boundary change and its evidence.
DR-0002's former automatic kernel-promotion and language-ownership rules are
superseded for v3.

## Required Lean and Quint formalization

Both lanes are intrinsic requirements of version 3:

~~~toml
[formalization]
scope = "docs/formalization.md"
gate = "tools/check_formal.py"
implementation_paths = ["src/checker", "src/boundary_adapter"]

[formalization.lean]
sources = ["formal/lean/Boundary.lean"]
toolchain = "leanprover/lean4:v4.34.1"
obligations = ["Boundary.admission_requires_evidence"]

[formalization.quint]
sources = ["formal/quint/boundary.qnt"]
toolchain = "@informalsystems/quint@0.33.1"
obligations = ["admissionInv", "validTraceTest"]
~~~

The paths above are illustrative. The adopter supplies actual files:

| Field | Meaning |
| --- | --- |
| scope | Existing document defining claims, assumptions, coverage, and limitations |
| gate | Existing repository-owned execution entrypoint, invoked by CI |
| implementation_paths | Nonempty existing file inventory for the implementation under the formal scope |
| lean.sources | Nonempty existing Lean source inventory |
| lean.toolchain | Pinned Lean toolchain |
| lean.obligations | Nonempty named declarations replayed by the gate |
| quint.sources | Nonempty existing Quint source inventory |
| quint.toolchain | Pinned Quint package version |
| quint.obligations | Nonempty named properties/tests exercised by the gate |

Paths must remain within the repository and identify files. Each consumer declares an exact toolchain version; floating selectors such as
latest do not satisfy the contract. Lean 4.34.1 and Quint 0.33.1 are the actual
estate-governance profile and the examples above, not a universal version mandate.
Toolchain changes require reviewed pin updates and fresh execution evidence.

There is no exemption Boolean or status label that substitutes for a required
lane. An empty directory, prose plan, unrelated example theorem, unused model,
or source file that the gate never checks cannot establish compliance.

### Scope and correspondence

The scope document must explain:

- the core boundary or correctness obligations being formalized;
- the named Lean statements and Quint properties, including their hypotheses;
- how declared implementation paths relate to the formal definitions;
- whether correspondence is machine-checked, supported by differential tests,
  argued in writing, assumed, or still open;
- unformalized behavior, unsupported features, and remaining obligations; and
- the exact limits of any finite or bounded exploration.

The requirement does not assert that a research repository has already solved
every conjecture. Open conjectures remain open. Its declared formal scope must
nevertheless contain real, relevant proofs and models.

A Lean differential execution lane is not automatically a Lean proof of another
implementation. Quint simulation, tests, bounded exploration, and symbolic
verification must be identified accurately; none becomes an unbounded theorem
by being placed in the formal directory.

### Execution requirements

The repository-owned gate must:

1. verify the declared toolchain identities;
2. replay the declared Lean obligations and record their axiom assumptions;
3. execute the declared Quint checks and record configuration, method, bounds,
   and seeds where applicable;
4. reject failures, missing or unrecognized outcomes, and unsupported evidence;
5. invalidate a previous success before starting a new attempt; and
6. record source identities before and after execution, failing on relevant drift.

An admitted proof or unreviewed project axiom cannot satisfy a declared Lean
obligation. Accepted foundational axioms and explicit hypotheses must be visible
in the scope/evidence. Evidence must identify the actual commands, toolchains,
source revision or content manifest, outcomes, and limits.

A required formal gate executes in the adopter's CI for the source under review.
Existing required contexts are preserved until a reviewed migration replaces them.
A selector must not silently omit the new formal obligations.

The static estate auditor validates the manifest, real artifact paths, and the
declared gate file. It does not establish that a workflow actually invokes that
file, execute arbitrary commands from the manifest, prove the scope document
accurate, or treat a declaration as a successful proof replay. CI wiring and
successful execution require their own inspected workflow and run evidence.
**Static contract validity and executed formal verification are separate results.**
A queued, cancelled, inaccessible, or unexecuted hosted job is not a passing result.

## Layout

No kernel plane, policy plane, or standard directory skeleton is mandatory in v3.
An adopter may keep its existing source layout. Do not create empty silos merely
to satisfy governance.

A plane inventory remains available when useful. Omit the layout section when
omitting that inventory; a layout status without an inventory is not a meaningful
mapping claim:

~~~toml
[layout]
status = "canonical"

[[plane]]
id = "implementation"
target = "src"
authority = "canonical_executable"
required = true
current = ["src"]

[[plane]]
id = "formalization"
target = "formal"
authority = "claim_state"
required = true
current = ["formal"]
~~~

This excerpt is not a complete inventory for every repository. If planes are
declared, their ids and targets must be unique, authority categories recognized,
and current mappings real. Required planes need mappings. A declared canonical
inventory must map its targets, cover all visible top-level directories under the
existing build-artifact exemptions, use no glob mappings, and have no pending
layout migration steps. Root-level documentation may accompany a mapped target.

Plane categories describe actual roles. They do not grant authority or require
separate implementation languages. Formal sources may use any declared real
paths; the formal directory name is a convention.

## Principles

~~~toml
[principles]
ordering = ["authority", "domain"]
disagreement = "fail_closed"
empty_silos = "forbidden"
generated_surfaces = "derived_only"
vendor_code = "non_local"
experimental_code = "non_authoritative"
~~~

Disagreement is defined by the affected contract, independently of the languages
involved. Explicitly registered differences need scoped expected outcomes;
unexpected differences do not silently pass.

Generated surfaces name their source. External code and auditors retain exact
provenance and remain distinct from local ownership. New vendoring is not
introduced by this revision. A computation is not a theorem merely because it
is deterministic or exhaustive. Moving a file changes neither mathematical
claims nor operational authority.

## Programs and shared components

Single-program repositories are the default. A multi-program repository uses
stable directory roots, unique ids and claim namespaces, identity-bound child
manifests, and explicit shared-component consumers.
[Multi-program contract v2](multi-program-repository-v2.md) removes the former
program-level canonical-language requirement.

The root authority and formalization declarations cover the repository. Child
metadata does not grant a separate undeclared boundary or establish formal
coverage. The scope document identifies the obligations and gaps across programs
and their shared components.

## External audit and pinning

Every adopter obtains the public governance auditor at its declared commit,
verifies SHA-256 against ESTATE.toml, and only then executes it. The pinning tool
sets those values from a chosen governance checkout:

~~~sh
python3 tools/pin_estate.py ../CONSUMER
python3 kernel/audit_estate_layout.py --root ../CONSUMER
python3 tools/pin_estate.py ../CONSUMER --check
~~~

Consumer CI uses the same pinned, verified audit path without exposing credentials
to PR-controlled code. The consumer also executes its own declared formal gate.
An auditor pin update does not change the manifest version or generate missing
proofs and models.

## Audit scope and refusal conditions

The static audit rejects invalid identity/version declarations, malformed pins,
unsupported estate positions, inconsistent boundary authority, missing or escaping
file paths, absent formal lanes, wrong toolchain declarations, empty obligation
inventories, missing gate declarations, and invalid declared layout/program
mappings. It preserves the legacy contract checks for legacy manifests.

These checks establish only their documented static scope. They do not infer
runtime correspondence, validate all human descriptions, transfer a proof
checker's authority, or replace the required formal execution gate.

## Migration and registry

V3 adoption is explicit and source-specific:

1. Inspect the consumer's actual boundary, implementation, and current evidence.
2. Replace language-based authority declarations with the boundary model.
3. Add real Lean and Quint artifacts, named obligations, and honest coverage.
4. Implement and execute the declared formal gate, then add it to CI.
5. Change to version 3 and update the exact governance pin in a reviewed change.
6. Regenerate registry records from the adopted source only when that registry
   update is in scope and its evidence is available.

Keep old pins and manifests replayable. V2 compatibility does not waive v3
requirements and must not be labeled current formal compliance. The committed
historical registry remains a record of its own source commits. Registry data
derived solely from manifests records declarations, not successful execution.

This governance revision does not repin consumers, alter their branch protections,
promote stages, or register new members. The new requirements are not satisfied
estate-wide merely because estate-governance implements them locally.

Lean-Goose is a concrete pending migration: its v2 scaffold and native Lean
differential comparison are recorded evidence, but a Lean proof of its intended
scope and a Quint model/gate must be supplied separately. The historical benchmark
must retain its original source attribution.
