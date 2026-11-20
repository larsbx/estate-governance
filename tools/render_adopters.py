#!/usr/bin/env python3
"""Render versioned adopter declarations without inferring formal compliance.

The default v1 registry continues to render its historical v2 contract table.
A separately generated registry-v2 requires an explicit --contract document;
it must never silently replace the historical table or invent a new membership
table in the current standard.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kernel"))
import audit_estate_registry as registry_audit  # noqa: E402

REGISTRY = ROOT / "policy" / "estate-registry.toml"
CONTRACT = ROOT / "docs" / "architecture" / "estate-repository-template-v2.md"
START = "<!-- generated: estate-adopters -->"
END = "<!-- /generated -->"


def render(data: dict | None = None) -> str:
    data = tomllib.loads(REGISTRY.read_text(encoding="utf-8")) if data is None else data
    version = registry_audit.registry_version(data)
    members = list(data["member"])
    members.sort(key=lambda m: (m["class"] == "meta", m["slug"]))

    rows = [
        "| Repository | Class | Layer | Band | Canonical language | Acceptance authority |",
        "| --- | --- | ---: | --- | --- | --- |",
    ] if version == 1 else [
        "| Repository | Class | Layer | Band | Manifest contract | Acceptance authority | Formalization evidence |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for member in members:
        manifest_version, template = registry_audit.validate_member_contract(member, version)
        layer = "outside" if member["class"] == "meta" else f"L{member['layer']}"
        acceptance = "yes" if member["acceptance_authority"] else "no"
        archived = " (archived)" if member["stage"] == "archived" else ""
        prefix = f"| `{member['slug']}`{archived} | {member['class']} | {layer} | {member['band']} | "
        if version == 1:
            rows.append(prefix + f"{member['canonical_language']} | {acceptance} |")
        else:
            evidence = ("Lean + Quint declared; not evaluated" if manifest_version == 3
                        else "Historical v2; not evaluated")
            rows.append(prefix + f"`{template}` | {acceptance} | {evidence} |")
    return "\n".join(rows)


def update(check: bool, *, registry: Path = REGISTRY, contract: Path | None = None) -> int:
    data = tomllib.loads(registry.read_text(encoding="utf-8"))
    version = registry_audit.registry_version(data)
    if version == 2 and contract is None:
        raise SystemExit("registry-v2 rendering requires an explicit --contract with generation markers")
    target = contract if contract is not None else CONTRACT
    if version == 2 and target.resolve() == CONTRACT.resolve():
        raise SystemExit("registry-v2 must not overwrite the historical v2 contract table")
    original = target.read_text(encoding="utf-8")
    if START not in original or END not in original:
        raise SystemExit("contract is missing adopter generation markers")
    before, rest = original.split(START, 1)
    _old, after = rest.split(END, 1)
    generated = f"{START}\n{render(data)}\n{END}"
    expected = before + generated + after
    if check:
        if original != expected:
            print("generated adopter table is stale")
            return 1
        print("generated adopter table is current")
        return 0
    target.write_text(expected, encoding="utf-8")
    print("generated adopter table updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--contract", type=Path,
                        help="target document; required for registry-v2, defaults to historical v2 for registry-v1")
    args = parser.parse_args()
    return update(args.check, registry=args.registry, contract=args.contract)


if __name__ == "__main__":
    raise SystemExit(main())
