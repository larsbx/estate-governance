# estate-governance

Canonical estate repository template (`estate-repository-v1`) for the larsbx
research estate: the contract, the manifest template, the layout audit, and the
tool that vendors them into consumer repositories.

```text
policy/estate.template.toml                          manifest template
kernel/audit_estate_layout.py                        estate-layout audit (canonical)
tools/vendor_estate.py                               vendor + pin into a consumer
docs/architecture/estate-repository-template-v1.md   the contract
tests/                                               audit and vendoring conformance
```

## Adopting the template

```sh
cp policy/estate.template.toml ../CONSUMER/estate.toml   # then fill it in
python tools/vendor_estate.py ../CONSUMER                # copy + pin at HEAD
python ../CONSUMER/tools/audit_estate_layout.py          # must pass; wire into CI
```

## Updating consumers after a template change

```sh
python tools/vendor_estate.py ../CONSUMER --check        # exit 1 on drift
python tools/vendor_estate.py ../CONSUMER                # re-vendor + re-pin
```

## Adopters

The adopter register is the Adopters section of
`docs/architecture/estate-repository-template-v1.md`.

## Checks

```sh
python kernel/audit_estate_layout.py
python -m pytest
```
