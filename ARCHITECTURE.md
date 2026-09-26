# Repository architecture

This repository is the canonical source of the estate repository template.

The machine-readable source of repository structure and authority is
[`estate.toml`](estate.toml). The reusable contract is
[`docs/architecture/estate-repository-template-v1.md`](docs/architecture/estate-repository-template-v1.md).

| Plane | Path | Content |
| --- | --- | --- |
| policy | `policy/` | the manifest template consumers start from |
| kernel | `kernel/` | the estate-layout audit, the one canonical implementation |
| conformance | `tests/` | one valid baseline and one rejecting mutation per audit rule |
| tooling | `tools/` | the vendoring tool that copies and pins the template in consumers |
| docs | `docs/` | the template contract |

Consumers never import from here at run time. They vendor byte-identical
copies and pin them by sha256 in their own `estate.toml`; the audit rejects any
local edit of a vendored copy.
