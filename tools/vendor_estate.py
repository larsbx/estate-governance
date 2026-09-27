#!/usr/bin/env python3
"""Vendor the estate template into a consumer repository and pin it.

Copies every file in the audit's VENDORED map from this checkout into the
consumer, then rewrites the consumer estate.toml [governance] table with this
checkout's commit and the sha256 of each copied file. With --check, writes
nothing and exits 1 when the consumer's copies or pin disagree with this
checkout.

Usage: vendor_estate.py CONSUMER_ROOT [--revision SHA] [--check]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kernel"))

from audit_estate_layout import GOVERNANCE_REPOSITORY, VENDORED, sha256  # noqa: E402

HEADER = re.compile(r"^\s*\[+\s*([A-Za-z0-9_.\"-]+)\s*\]+")


def head_revision() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def governance_block(revision: str, digests: dict[str, str]) -> str:
    rows = "".join(f'"{rel}" = "{digest}"\n' for rel, digest in sorted(digests.items()))
    return (
        "[governance]\n"
        f'repository = "{GOVERNANCE_REPOSITORY}"\n'
        f'revision = "{revision}"\n\n'
        "[governance.sha256]\n"
        f"{rows}"
    )


def without_governance(text: str) -> str:
    """Drop the [governance] table and its subtables, keeping every other line."""
    kept, inside = [], False
    for line in text.splitlines(keepends=True):
        if match := HEADER.match(line):
            inside = match.group(1).split(".")[0] == "governance"
        if not inside:
            kept.append(line)
    return "".join(kept).rstrip() + "\n"


def pin(text: str, revision: str, digests: dict[str, str]) -> str:
    return f"{without_governance(text)}\n{governance_block(revision, digests)}"


def vendor(consumer: Path, revision: str) -> None:
    for local, source in VENDORED.items():
        target = consumer / local
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / source).read_bytes())
    manifest = consumer / "estate.toml"
    digests = {local: sha256(consumer / local) for local in VENDORED}
    manifest.write_text(pin(manifest.read_text(encoding="utf-8"), revision, digests), encoding="utf-8")


def drift(consumer: Path) -> list[str]:
    expected = {local: sha256(ROOT / source) for local, source in VENDORED.items()}
    pinned = tomllib.loads((consumer / "estate.toml").read_text(encoding="utf-8")).get("governance", {})
    return [
        local
        for local, digest in expected.items()
        if not (consumer / local).is_file()
        or sha256(consumer / local) != digest
        or pinned.get("sha256", {}).get(local) != digest
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("consumer", type=Path)
    parser.add_argument("--revision", help="governance commit to pin (default: HEAD)")
    parser.add_argument("--check", action="store_true", help="report drift, write nothing")
    args = parser.parse_args(argv)
    consumer = args.consumer.resolve()

    if args.check:
        stale = drift(consumer)
        for rel in stale:
            print(f"estate template drift: {rel}", file=sys.stderr)
        return 1 if stale else 0

    vendor(consumer, args.revision or head_revision())
    print(f"vendored estate template into {consumer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
