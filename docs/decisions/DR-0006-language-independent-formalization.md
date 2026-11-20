# DR-0006 — Unrestricted implementation languages and required Lean/Quint formalization

- **Status:** accepted
- **Implementation:** versioned contract change staged in a PR; consumer adoption remains explicit
- **Date:** 2026-11-20
- **Decides for:** estate repository standards
- **Supersedes:** v2 language-role requirements, DR-0001's language-only position-change approval clause, and DR-0002's language-ownership and automatic kernel-authority promotion rules
- **Preserves:** explicit domain boundaries, dependency provenance, DR-0004 evidence discipline, and DR-0005 CI ownership and check-migration discipline

## Owner instruction

The owner directed that the estate governance standards be revised because the
different language requirements are no longer needed, and that Lean/Quint
formalization become a requirement. This record adopts that direction. The
implementation of a versioned contract in a PR does not by itself migrate the
estate or establish successful formal checks for its members.

## Decision

Implementation languages are unrestricted. A repository or program need not name
one canonical language, give it a kernel role, or classify other languages as
supporting. Language choice does not confer or prevent acceptance authority.

A repository explicitly declares whether it owns acceptance/effect boundaries.
When it does, it names each boundary, its contract, and the existing implementation
files. A boundary implementation may combine languages. A repository with no
owned accepting boundary declares that absence. Adding a kernel, changing a
directory name, or landing a new implementation does not automatically grant
authority.

Lean and Quint are both required for v3 formalization. Each adopter supplies
actual proof/model sources, pinned toolchains, named obligations, an executable
repository-owned gate invoked by CI, and a scope document connecting those
obligations to implementation paths. The scope document records assumptions,
open work, and correspondence limits. A plan or status flag cannot substitute
for either lane.

The Lean gate replays the declared proof obligations and reports its axiom
assumptions. The Quint gate executes the declared checks and records the
exploration method and its limits. Bounded checks are reported as bounded checks,
not universal proofs. Required checks produce evidence bound to the source and
toolchain used. Static manifest validation and executed formal evidence remain
distinct results.

## Layout and versioning

The new contract is
[estate-repository-v3](../architecture/estate-repository-template-v3.md).
A plane inventory is optional; an adopter need not create empty kernel or policy
directories. Declared mappings are still checked, and a declared canonical
inventory must be complete.

Earlier v2 contracts and exact-revision evidence remain replayable. They are
legacy records, not evidence of v3 compliance. Consumer updates must explicitly
change the manifest version, implement the formal obligations, reproduce the
gates, and update the governance pin. No bulk repin or generated-registry rewrite
is authorized by this policy decision.

## Effect on DR-0001

DR-0001's adopted class, layer, band, and INV positions remain in force. For v3,
changing an implementation-language assignment alone no longer requires a new
estate position decision. The old language column remains historical evidence.
Actual boundary, behavior, dependency, and formal-scope changes still undergo
their applicable review and verification; removing the language restriction does
not bypass those obligations.

## Effect on DR-0002

The following former requirements cease to apply to v3:

- Exactly one canonical language owns all repository acceptance authority.
- A canonical language must have the kernel role.
- Supporting languages cannot participate in an accepting implementation.
- Every new kernel automatically changes the repository to accepting authority.
- A non-accepting repository needs a special language/kernel exception.

DR-0002 remains part of the historical v2 contract. Its useful distinction between
domain acceptance and mathematical proof is retained in v3. Existing source
repositories' named boundaries are not silently withdrawn or expanded.

## Initial implementation and remaining adoption

Estate-governance implements v3 declarations, static audit coverage, and its own
Lean/Quint evidence model. That formal scope does not establish full correspondence
with all Python runtime code or all consumer implementations.

Lean-Goose was scaffolded under v2 before this revision. Its external native Lean
differential checker is comparison evidence; it is not a Lean proof of Goose
correctness, and it does not supply a Quint model. Lean-Goose therefore needs a
separate v3 migration with actual scoped formal artifacts and execution evidence.
The same evidence rule applies to every other consumer.

## Consequences

1. Remove mandatory language-role and artificial-kernel rules from the current
   contract, validators, templates, and future migration goals.
2. Retain versioned legacy interpretation and disclose unassessed formal coverage
   in registry projections.
3. Require substantive Lean and Quint artifacts and executable verification for
   new v3 adoption.
4. Preserve existing required CI contexts until their replacement is reviewed;
   a queued, inaccessible, cancelled, or unexecuted job is not a successful check.
5. Keep authority changes, membership changes, stage promotion, and consumer pin
   updates explicit. A passing formal model does not perform any of those actions.
