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
| docs | `docs/` | the template contract |

Consumers never import or copy anything from here. Their CI checks this
repository out at the commit their `ESTATE.toml` pins and runs the audit from that
checkout; the audit verifies its own sha256 against the consumer's pin.
