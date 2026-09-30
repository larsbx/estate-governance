# Repository architecture

This repository is the canonical source of the estate repository template.

The machine-readable source of repository structure and authority is
[`ESTATE.toml`](ESTATE.toml). The reusable contract is
[`docs/architecture/estate-repository-template-v2.md`](docs/architecture/estate-repository-template-v2.md).

| Plane | Path | Content |
| --- | --- | --- |
| policy | `policy/` | the manifest template consumers start from |
| kernel | `kernel/` | the estate audit, the one canonical implementation |
| conformance | `tests/` | one valid baseline and one rejecting mutation per audit rule |
| tooling | `tools/` | the tool that pins a consumer to a governance commit |
| docs | `docs/` | the base template and multi-program extension contracts |

Consumers never import or copy anything from here. Their CI checks this
repository out at the commit their `ESTATE.toml` pins and runs the audit from that
checkout; the audit verifies its own sha256 against the consumer's pin.

## Repository shapes

The v2 contract supports the existing single-program shape and an additive
multi-program shape. Multi-program repositories bind durable concerns to
`programs/<id>/PROGRAM.toml`; branches remain temporary change lines. See
[`multi-program-repository-v1.md`](docs/architecture/multi-program-repository-v1.md).
