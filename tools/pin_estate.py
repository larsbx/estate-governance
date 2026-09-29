#!/usr/bin/env python3
"""Pin a consumer's estate dependencies in its ESTATE.toml.

Sets the [[dep]] "estate-governance" entry to this checkout's commit (`rev`)
and the sha256 of its audit (`pin`), which is what the audit verifies about
itself when CI runs it from a checkout of that commit; and sets the `pin` of
every [[dep]] the consumer vendors packages from to the digest of those
packages in its vendored.toml. Only those `rev` and `pin` lines change. With
--check, writes nothing and exits 1 when a pin would change.

Usage: pin_estate.py CONSUMER_ROOT [--revision SHA] [--check]
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

from audit_estate_layout import GOVERNANCE_ID, MANIFEST, sha256, vendored_digest  # noqa: E402

HEADER = re.compile(r"^\s*\[")
FIELD = re.compile(r'^(?P<key>pin|rev)(?P<eq>\s*=\s*)"[^"]*"(?P<rest>.*)$')


def head_revision() -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()


def wanted(consumer: Path, revision: str) -> dict[str, dict[str, str]]:
    """dep id -> the rev/pin values it should carry."""
    out = {GOVERNANCE_ID: {"rev": revision, "pin": "sha256:" + sha256(ROOT / "kernel" / "audit_estate_layout.py")}}
    vendored = consumer / "vendored.toml"
    if vendored.is_file():
        for source in {p["repository"] for p in tomllib.loads(vendored.read_text(encoding="utf-8")).get("package", [])}:
            out[source.split("/")[1]] = {"pin": "sha256:" + vendored_digest(consumer, source)}
    return out


def rewrite(text: str, values: dict[str, dict[str, str]]) -> str:
    deps = {d.get("id") for d in tomllib.loads(text).get("dep", [])}
    missing = sorted(set(values) - deps)
    if missing:
        raise SystemExit(f"{MANIFEST} lacks [[dep]] entries for: {', '.join(missing)}")
    lines, block, dep_id = [], None, None
    for line in text.splitlines(keepends=True):
        if HEADER.match(line):
            block, dep_id = line.split("#", 1)[0].strip(), None
        elif block == "[[dep]]" and (m := re.match(r'^id\s*=\s*"([^"]+)"', line)):
            dep_id = m.group(1)
        elif block == "[[dep]]" and dep_id in values and (m := FIELD.match(line.rstrip("\n"))):
            key = m.group("key")
            if key in values[dep_id]:
                line = f'{key}{m.group("eq")}"{values[dep_id][key]}"{m.group("rest")}\n'
        lines.append(line)
    return "".join(lines)


def pin(consumer: Path, revision: str) -> str:
    manifest = consumer / MANIFEST
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    new = rewrite(text, wanted(consumer, revision))
    got = {d["id"]: d for d in tomllib.loads(new).get("dep", [])}
    for dep_id, fields in wanted(consumer, revision).items():
        for key, value in fields.items():
            if got[dep_id].get(key) != value:
                raise SystemExit(f"[[dep]] {dep_id} has no {key} line to pin")
    manifest.write_text(new, encoding="utf-8")
    return new


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("consumer", type=Path)
    parser.add_argument("--revision", help="governance commit to pin (default: HEAD)")
    parser.add_argument("--check", action="store_true", help="report drift, write nothing")
    args = parser.parse_args(argv)
    consumer, revision = args.consumer.resolve(), args.revision or head_revision()
    if args.check:
        text = (consumer / MANIFEST).read_text(encoding="utf-8")
        drift = rewrite(text, wanted(consumer, revision)) != text
        if drift:
            print(f"estate pins drift in {consumer / MANIFEST}", file=sys.stderr)
        return 1 if drift else 0
    pin(consumer, revision)
    print(f"pinned estate dependencies of {consumer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
