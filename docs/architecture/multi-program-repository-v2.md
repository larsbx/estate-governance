# Multi-program repository contract v2

Status: extension of
[estate-repository-v3](estate-repository-template-v3.md).
Supersedes multi-program v1 for explicit v3 adopters.

Durable concerns within one repository are directory-rooted programs. Branches
remain temporary change lines. Implementation languages are unrestricted, and
program declarations no longer require a canonical language.

## Root declarations

~~~toml
[workspace]
mode = "multi_program"

[[program]]
id = "first-program"
root = "programs/first-program"
manifest = "PROGRAM.toml"
claim_namespace = "FIRST"

[[program]]
id = "second-program"
root = "programs/second-program"
manifest = "PROGRAM.toml"
claim_namespace = "SECOND"

[[shared_component]]
id = "shared-core"
root = "shared/shared-core"
consumers = ["first-program", "second-program"]
~~~

A multi-program workspace declares at least two programs. Each has a unique,
stable id, repository-relative root under programs/, uppercase claim namespace,
and identity-bound PROGRAM.toml. Shared components use roots under shared/ and
name nonempty sets of known consuming programs.

The root manifest remains the authority for repository identity, boundaries,
dependency pins, and formalization. Program language metadata, if retained for
description, grants no authority.

## Child identity

The child format remains version 1; changing the root contract does not require
rewriting child history:

~~~toml
version = 1

[program]
id = "first-program"

[status]
lifecycle = "active"
theorem_status_source = "formal/claims.toml"

[paths]
implementation = "src"
formal = "formal"
docs = "docs"
tests = "tests"
~~~

Status/path fields describe the actual program. They do not turn a claim into a
theorem, supply missing formal artifacts, or require a placeholder kernel folder.
Use the [child template](../../policy/PROGRAM.template.toml) as a starting point.

The audit checks root/child identity agreement, real roots and child manifests,
non-escaping paths, uniqueness, and known shared-component consumers. Historical
v2 root manifests continue to use the former multi-program contract.

## Authority and formalization

The root [authority] declaration and named boundaries apply across all programs.
Each accepting boundary identifies its actual implementation files and contract,
which may span a program and shared components. A false root declaration means
that no program owns an undeclared accepting boundary.

Both formal lanes remain required at the repository level. Root formalization
sources and implementation_paths identify the checked artifacts; the scope
document maps obligations to the programs and shared components they concern.
Shared source changes must invalidate affected evidence.

A proof for one program is not automatically a proof for its consumers. A passing
Quint model is not a correspondence theorem for every implementation. Disclose
partial coverage, assumptions, open obligations, and bounded checks without
claiming that unrepresented programs have passed.

## Layout inventory

V3 does not require collection-plane entries solely because programs exist.
If an optional plane inventory is declared, it must describe the actual layout
under the same rules as any v3 repository. A canonical inventory must cover the
programs/ and shared/ top-level directories when they exist. Suitable authority
categories are program_collection and shared_component_collection.

Do not create empty program or shared directories for an unimplemented migration.
Declare real roots and keep proposed movements in the migration plan.

## Migration

1. Inspect current boundaries, formal coverage, source provenance, and dependency
   relationships.
2. Add or update real program identities without inventing authority.
3. Preserve source history when importing existing programs.
4. Reconcile shared components behind documented interfaces and consumer lists.
5. Add the Lean/Quint obligations and gates for the declared combined scope.
6. Reproduce affected original gates and new formal evidence before adoption.
7. Transfer or cross-link issues/releases and archive source repositories only
   through separately authorized changes with durable redirects.

No mass move, source archival, language rewrite, or authority promotion follows
from adopting this contract.
