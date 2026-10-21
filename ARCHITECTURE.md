# Repository architecture

This repository is the canonical source of the estate repository template.

The machine-readable source of repository structure and authority is
[`ESTATE.toml`](ESTATE.toml). The reusable contract is
[`docs/architecture/estate-repository-template-v2.md`](docs/architecture/estate-repository-template-v2.md).

| Plane | Path | Content |
| --- | --- | --- |
| policy | `policy/` | manifest/program templates plus the estate-wide member/graph registry |
| kernel | `kernel/` | canonical repository-local and estate-wide governance audits |
| conformance | `tests/` | valid baselines and rejecting mutations for both audit scopes |
| tooling | `tools/` | consumer pinning, registry generation/freshness checks and adopter rendering |
| docs | `docs/` | the base template and multi-program extension contracts |

Consumers never treat governance code as domain authority. Their CI runs the
repository-local audit from the exact governance revision and SHA-256 declared in
`ESTATE.toml`.

Estate-wide state is separate: `policy/estate-registry.toml` records exact member
snapshots and cross-repository facts, while `kernel/audit_estate_registry.py`
checks graph direction/acyclicity, global name ownership, governance freshness,
stage values, and estate-gate presence. Reciprocal conformance is permitted and
is not confused with a code dependency.

The independent CI freshness job uses `tools/check_registry_freshness.py` to
acquire immutable member observations, reproduce the exact recorded sources and
compare their manifest bytes and generated facts with captured `main` heads.
Its explicit policy, self-reference rule, evidence receipts and access failures
are defined in [registry freshness v1](docs/architecture/registry-freshness-v1.md).

## Repository shapes

The v2 contract supports the existing single-program shape and an additive
multi-program shape. Multi-program repositories bind durable concerns to
`programs/<id>/PROGRAM.toml`; branches remain temporary change lines. See
[`multi-program-repository-v1.md`](docs/architecture/multi-program-repository-v1.md).
