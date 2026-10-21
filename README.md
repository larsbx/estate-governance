# estate-governance

Canonical estate repository template (`estate-repository-v2`) for the larsbx
research estate: the contract, the manifest template, the audit, and the tool that
pins consumers to it. v2 carries the SPEC_estate v0.1 manifest in `ESTATE.toml`;
consumers check this repository out at a pinned commit instead of vendoring it.

```text
policy/ESTATE.template.toml                          manifest template
policy/estate-registry.toml                          estate-wide membership/graph snapshot
kernel/audit_estate_layout.py                        one-repository audit
kernel/audit_estate_registry.py                      estate-wide graph/uniqueness/freshness audit
tools/pin_estate.py                                  pin a consumer to this checkout
tools/snapshot_registry.py                           regenerate the registry from members' manifests
tools/check_registry_freshness.py                    capture source revisions and check snapshot freshness
tools/render_adopters.py                             render the contract adopter table
docs/decisions/                                      owner decision records (DR-nnnn)
docs/architecture/estate-repository-template-v2.md   the contract (v1 kept, superseded)
policy/PROGRAM.template.toml                       child manifest for multi-program repositories
docs/architecture/multi-program-repository-v1.md    monorepo extension contract
tests/                                               audit and pinning conformance
```

## Repository shapes

Single-program repositories remain the default. A repository that consolidates
durable research concerns declares `[workspace] mode = "multi_program"` and lists
directory-rooted `[[program]]` entries. Long-lived branches are not program
boundaries. See the multi-program contract.

## Adopting the template

```sh
cp policy/ESTATE.template.toml ../CONSUMER/ESTATE.toml   # then fill it in
python tools/pin_estate.py ../CONSUMER                   # pin rev + audit digest at HEAD
python kernel/audit_estate_layout.py --root ../CONSUMER  # must pass; wire the CI step into CI
```

The consumer's CI downloads the audit from this public repository at the pinned commit,
verifies its SHA-256 against the manifest pin, and runs it without any repository secret
(see the contract).

## Updating consumers after a template change

```sh
python tools/pin_estate.py ../CONSUMER --check           # exit 1 on drift
python tools/pin_estate.py ../CONSUMER                   # re-pin
```

## Adopters

`policy/estate-registry.toml` is the machine-readable membership source, generated
from members' manifests by `python tools/snapshot_registry.py` (run with sibling
checkouts; `--check` reports drift). CI also checks exact provenance and manifest
freshness against captured source heads, with the tested commit used for this
repository. See the [freshness policy and access requirements](docs/architecture/registry-freshness-v1.md).
Unavailable sources fail the gate; a valid registry alone is insufficient.
The Adopters section of
`docs/architecture/estate-repository-template-v2.md` is a generated projection of it,
and CI rejects drift between them.

## Checks

```sh
python kernel/audit_estate_layout.py
python kernel/audit_estate_registry.py
python tools/render_adopters.py --check
python -m pytest

# Live cross-repository check (a new directory; source access required):
python tools/check_registry_freshness.py --fetch --sources /tmp/estate-observation-1
```
