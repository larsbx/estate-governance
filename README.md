# estate-governance

Canonical estate repository template (`estate-repository-v2`) for the larsbx
research estate: the contract, the manifest template, the audit, and the tool that
pins consumers to it. v2 carries the SPEC_estate v0.1 manifest in `ESTATE.toml`;
consumers check this repository out at a pinned commit instead of vendoring it.

```text
policy/ESTATE.template.toml                          manifest template
kernel/audit_estate_layout.py                        estate audit (canonical, never vendored)
tools/pin_estate.py                                  pin a consumer to this checkout
docs/architecture/estate-repository-template-v2.md   the contract (v1 kept, superseded)
tests/                                               audit and pinning conformance
```

## Adopting the template

```sh
cp policy/ESTATE.template.toml ../CONSUMER/ESTATE.toml   # then fill it in
python tools/pin_estate.py ../CONSUMER                   # pin rev + audit digest at HEAD
python kernel/audit_estate_layout.py --root ../CONSUMER  # must pass; wire the CI step into CI
```

The consumer's CI downloads a public, immutable mirror of the audit, verifies its\nSHA-256 against the manifest pin, and runs it without any repository secret (see the contract).

## Updating consumers after a template change

```sh
python tools/pin_estate.py ../CONSUMER --check           # exit 1 on drift
python tools/pin_estate.py ../CONSUMER                   # re-pin
```

## Adopters

The adopter register is the Adopters section of
`docs/architecture/estate-repository-template-v2.md`.

## Checks

```sh
python kernel/audit_estate_layout.py
python -m pytest
```
