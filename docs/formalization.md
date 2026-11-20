# Formal evidence lifecycle

This repository supplies both Lean and Quint formalization for the v3 evidence
lifecycle. Production implementation languages are unrestricted. The formal
scope is the rule for treating two required verification results as current,
including invalidation and preservation of domain authority.

## What is formalized

The model state contains source and policy identities, separate Lean and Quint
observations, a verification flag, and a domain-authority flag. Each observation
is missing, queued, running, passed, or failed. Current evidence must report a
pass and match both current identities. Verification requires both lanes.

Transitions record a result, revise the source or policy, verify a ready state,
or leave it unchanged. Recording any replacement result or changing either
identity clears the prior verification flag. No transition changes domain
authority. Source and policy identities are abstract natural numbers in Lean;
the executable gate binds actual input bytes with SHA-256. The formal model
does not establish the cryptographic or operating-system assumptions behind
that binding.

### Lean obligations

`formal/lean/EstateFormal.lean` proves seventeen named obligations. The principal
claims declared in `ESTATE.toml` are:

| Theorem | Claim |
| --- | --- |
| `EstateFormal.ready_requires_both` | Readiness requires passed Lean and Quint observations |
| `EstateFormal.stale_lean_source_not_ready` | A stale Lean source identity prevents readiness |
| `EstateFormal.stale_quint_policy_not_ready` | A stale Quint policy identity prevents readiness |
| `EstateFormal.revise_source_invalidates` | Revising source clears prior verification |
| `EstateFormal.revise_policy_invalidates` | Revising policy clears prior verification |
| `EstateFormal.transition_preserves_verified` | Every permitted transition preserves verification safety |
| `EstateFormal.reachable_verified_requires_both` | Every reachable verified state has both current passed observations |
| `EstateFormal.transition_preserves_authority` | A single evidence transition preserves domain authority |
| `EstateFormal.reachable_preserves_authority` | Every reachable state retains initial domain authority |

Additional obligations establish exact source/policy agreement for both lanes,
refusal of nonpassing results, invalidation by replacement observations, initial
safety, and a concrete verified state without domain authority.

The induction theorem is unbounded over the model's reachable traces.
`formal/lean/Audit.lean` requires the complete seventeen-theorem inventory and
checks that those theorems transitively depend on no axioms. It also audits
every declaration in the `EstateFormal` namespace; only `propext`, used by
Lean-generated structure support, is permitted there. Application axioms and
`sorryAx` fail the audit.

### Quint obligations and bounds

`formal/quint/EstateFormal.qnt` executes the corresponding lifecycle. Its
`safety` invariant states that verification implies both current passed lanes
and that the initially false domain-authority flag remains false.

Nine deterministic tests cover missing evidence, both lanes, a single lane,
stale source, stale policy, failed replacement, queued replacement, authority
preservation, and recovery after both identities change. The gate additionally
simulates **1,000 traces of at most 40 transitions**, using seed `20261120` and
the TypeScript backend. Source and policy revisions range from zero through
two in these simulations. A successful run means no violation was found in
those bounded traces; it is not exhaustive exploration or an unbounded Quint
proof.

The intentionally incorrect `unsafeStep` sets verification without checking
either lane. A separate one-transition run must exit with the designated
invariant failure and emit the two-state witness in
`formal/evidence/quint-negative.itf.json`. A parse error, type error, missing
tool, or arbitrary nonzero exit does not satisfy this negative control.

## Reproduction

Use Python 3.11+, Lean `leanprover/lean4:v4.34.1`, and Quint
`@informalsystems/quint@0.33.1`. The checked Lean revision is
`5045d0056413266e57c625dcd7c365b10e377c52`. The workflow uses Node `24.22.3`.

```sh
npm --prefix formal/quint ci --ignore-scripts --no-audit --no-fund
LEAN=/absolute/path/to/lean-4.34.1/bin/lean python3 tools/check_formal.py
```

`LEAN` defaults to `lean` on PATH. Quint defaults to the installation under
`formal/quint/node_modules`; `QUINT` can name another installed CLI, whose
reported version and executable identity are recorded. Dependencies are not
vendored. `formal/quint/package-lock.json` pins the reproducible npm install.

The gate builds the local Lean source in a fresh temporary directory and runs
the axiom audit against that new object. It then runs actual Quint typechecking,
all deterministic tests, bounded invariant simulation, and the negative
control. The workflow runs unconditionally on pull requests, pushes to main,
merge groups, and manual dispatch.

## Receipt contract

`formal/evidence/results.json` has schema `estate.formal-evidence.v1`. It records
the full repository source manifest and digest, manifest-policy hash, tool
versions and executable hashes, executed command vectors and hashes, logs,
theorem inventory, Quint bounds, negative witness, and before/after identity
checks. Generated evidence, dependency installations, and build outputs are
excluded from the source digest. The source manifest lists the bytes actually
covered. Every declared scope, gate, implementation, formal source, and profile
file must appear in both source inventories; declaring an input under an
excluded directory or with an excluded suffix fails verification. A custom
`--output` directory may be under `formal/evidence` or outside
the repository.

The gate writes `running` before reading sources, configuration, or executables,
so a new failure cannot leave an earlier `passed` receipt in place. Command
failure, missing obligations, changed sources, or changed executable bytes
produce a failed receipt and nonzero exit. Queued hosted work is never recorded
as passed local execution. CI preserves receipts and logs as artifacts.

## Correspondence and remaining obligations

These are formal statements about the declared lifecycle model. The Python
layout auditor and receipt wrapper are bound into the source digest, but their
behavior is **not proved to refine the Lean model**. The Lean-to-Quint model
correspondence is reviewed and exercised, not proved by a translation theorem.
Authenticity of tool outcomes, filesystem consistency between reads, external
runner behavior, and SHA-256 assumptions remain in the execution boundary.

The formal gate does not establish domain proofs for other repositories,
estate-wide v3 adoption, or theorem/declaration/deployment admission authority.
Every adopter must supply its own scoped Lean and Quint obligations and
execution evidence. Files or a passing static manifest audit alone do not meet
the execution requirement.
