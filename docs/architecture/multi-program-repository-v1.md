# Multi-program research repository contract

Status: additive extension to estate-repository-v2.

## Decision

Durable mathematical concerns are directory-rooted programs on the default branch.
Git branches remain temporary change lines and are not program containers.

A repository opts in with `[workspace] mode = "multi_program"`. Existing repositories
default to `single` and require no changes.

## Layout

```text
repository/
├── ESTATE.toml
├── ARCHITECTURE.md
├── programs/
│   ├── finite-dynamics/
│   │   ├── PROGRAM.toml
│   │   ├── kernel/
│   │   ├── proof/
│   │   ├── docs/
│   │   └── tests/
│   └── tiling-theory/
│       └── ...
├── shared/
│   └── finite-math-kernels/
└── tools/
```

The `programs` and `shared` roots are claimed by explicit collection planes, so canonical coverage remains total. The root is program-first only at the workspace boundary. Authority remains first
inside each program: canonical kernel, claim state, evidence, exposition, and
experiments stay explicitly separated.

## Root declarations

```toml
[workspace]
mode = "multi_program"

[[plane]]
id = "programs"
target = "programs"
authority = "program_collection"
required = true
current = ["programs"]

[[plane]]
id = "shared"
target = "shared"
authority = "shared_component_collection"
required = true
current = ["shared"]

[[program]]
id = "finite-dynamics"
root = "programs/finite-dynamics"
manifest = "PROGRAM.toml"
claim_namespace = "FD"
canonical_language = "Mojo"

[[program]]
id = "tiling-theory"
root = "programs/tiling-theory"
manifest = "PROGRAM.toml"
claim_namespace = "TT"
canonical_language = "Mojo"

[[shared_component]]
id = "finite-math-kernels"
root = "shared/finite-math-kernels"
consumers = ["finite-dynamics", "tiling-theory"]
```

Each program has a unique stable id, directory root, uppercase claim namespace,
canonical language, and identity-bound `PROGRAM.toml`. Shared components explicitly
name their consuming programs; an undeclared consumer fails the audit.

Program-local `canonical_language` declarations describe code ownership and do not
grant acceptance authority. The root canonical language's `acceptance_authority`
declaration in `ESTATE.toml` governs the whole repository: `false` means that no
program or shared component owns an acceptance or effect boundary. Programs that
perform oracle work may use canonical local kernels under that zero-authority model.

The audit rejects path traversal, missing roots or child manifests, duplicate ids,
roots or claim namespaces, child identity disagreement, fewer than two programs,
and shared components with empty or unknown consumer sets.

## Migration sequence

1. Add declarations and empty receiving boundaries without changing authority.
2. Import each source repository with history preserved.
3. Reconcile duplicate shared code behind explicit component interfaces.
4. Move CI to path-aware program and reverse-dependency gates.
5. Transfer or cross-link issues and releases.
6. Archive source repositories with immutable redirect READMEs.

The initial pilot is the finite-dynamics family: finite Mandelbrot, finite Julia,
bulb/Ford-circle research, and the Julia oracle. No source repository is archived
until the consolidated program passes its original gates and provenance checks.
