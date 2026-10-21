#!/usr/bin/env python3
"""Render the adopter table in the v2 contract from policy/estate-registry.toml."""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "policy" / "estate-registry.toml"
CONTRACT = ROOT / "docs" / "architecture" / "estate-repository-template-v2.md"
START = "<!-- generated: estate-adopters -->"
END = "<!-- /generated -->"


def render() -> str:
    data = tomllib.loads(REGISTRY.read_text(encoding="utf-8"))
    members = list(data["member"])
    members.sort(key=lambda m: (m["class"] == "meta", m["slug"]))

    rows = [
        "| Repository | Class | Layer | Band | Canonical language | Acceptance authority |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for member in members:
        layer = "outside" if member["class"] == "meta" else f"L{member['layer']}"
        acceptance = "yes" if member["acceptance_authority"] else "no"
        rows.append(
            f"| `{member['slug']}` | {member['class']} | {layer} | "
            f"{member['band']} | {member['canonical_language']} | {acceptance} |"
        )
    return "\n".join(rows)


def update(check: bool) -> int:
    original = CONTRACT.read_text(encoding="utf-8")
    if START not in original or END not in original:
        raise SystemExit("contract is missing adopter generation markers")
    before, rest = original.split(START, 1)
    _old, after = rest.split(END, 1)
    generated = f"{START}\n{render()}\n{END}"
    expected = before + generated + after
    if check:
        if original != expected:
            print("generated adopter table is stale")
            return 1
        print("generated adopter table is current")
        return 0
    CONTRACT.write_text(expected, encoding="utf-8")
    print("generated adopter table updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return update(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
