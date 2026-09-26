#!/usr/bin/env python3
"""Validate the estate repository architecture manifest (estate-repository-v1).

Canonical source: larsbx/estate-governance, kernel/audit_estate_layout.py.
Consumers carry a byte-identical copy at tools/audit_estate_layout.py, pinned
by sha256 in the [governance] table of their estate.toml. Never edit a
vendored copy; change the source and re-vendor.

This audit is intentionally domain-agnostic. Domain theorem status and
certificate acceptance remain consumer responsibilities.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GOVERNANCE_REPOSITORY = "larsbx/estate-governance"

#: Consumer path -> source path in the governance repository.
VENDORED: dict[str, str] = {
    "tools/audit_estate_layout.py": "kernel/audit_estate_layout.py",
    "docs/architecture/estate-repository-template-v1.md": "docs/architecture/estate-repository-template-v1.md",
}

ENTRYPOINTS = ("ARCHITECTURE.md", "docs/architecture/estate-repository-template-v1.md")

ALLOWED_PLANE_AUTHORITIES = frozenset({
    "governance",
    "canonical_executable",
    "claim_state",
    "non_authoritative_reference",
    "non_authoritative_oracle",
    "non_authoritative_experiment",
    "contract",
    "evidence",
    "pinned_external",
    "repository_tooling",
    "exposition",
    "publication",
    "example",
})
ALLOWED_LANGUAGE_AUTHORITIES = frozenset({"canonical", "supporting"})


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: object, message: str) -> None:
    if not condition:
        fail(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path | None = None) -> dict:
    path = path or ROOT / "estate.toml"
    require(path.is_file(), f"missing estate manifest: {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def validate_identity(data: dict) -> str:
    require(data.get("version") == 1, "estate.toml version must be 1")
    require(data.get("template") == "estate-repository-v1",
            "estate.toml template must be estate-repository-v1")
    repository = data.get("repository", {})
    repository_id = repository.get("id", "")
    require(re.fullmatch(r"[^/\s]+/[^/\s]+", repository_id),
            "repository.id must be OWNER/REPOSITORY")
    require(repository.get("layout_status") in {"transitional", "canonical"},
            "repository.layout_status must be transitional or canonical")
    return repository_id


def validate_principles(data: dict) -> None:
    principles = data.get("principles", {})
    require(principles.get("ordering") == ["authority", "domain", "language"],
            "principles.ordering must be authority, domain, language")
    require(principles.get("cross_language_disagreement") == "fail_closed",
            "cross-language disagreement must fail closed")
    require(principles.get("empty_silos") == "forbidden", "empty silos must be forbidden")


def validate_planes(data: dict, root: Path) -> None:
    planes = data.get("plane", [])
    require(planes, "at least one authority plane is required")

    ids: set[str] = set()
    targets: set[str] = set()
    for plane in planes:
        plane_id, target = plane.get("id", ""), plane.get("target", "")
        require(plane_id, "plane.id is required")
        require(plane_id not in ids, f"duplicate plane id: {plane_id}")
        require(target, f"plane {plane_id}: target is required")
        require(target not in targets, f"duplicate plane target: {target}")
        ids.add(plane_id)
        targets.add(target)
        require(plane.get("authority") in ALLOWED_PLANE_AUTHORITIES,
                f"plane {plane_id}: unknown authority {plane.get('authority')!r}")

        current = plane.get("current", [])
        current_globs = plane.get("current_globs", [])
        require(not plane.get("required", False) or current or current_globs,
                f"plane {plane_id}: required plane needs a current mapping")
        for rel in current:
            require((root / rel).exists(), f"plane {plane_id}: missing current path {rel}")
        for pattern in current_globs:
            require(glob.glob(str(root / pattern), recursive=True),
                    f"plane {plane_id}: current_globs pattern matches nothing: {pattern}")

    for mandatory in ("kernel", "policy"):
        require(mandatory in ids, f"{mandatory} plane is required for this template")


def validate_languages(data: dict) -> None:
    names: set[str] = set()
    for language in data.get("language", []):
        name, authority = language.get("name", ""), language.get("authority", "")
        require(name, "language.name is required")
        require(name not in names, f"duplicate language: {name}")
        names.add(name)
        require(authority in ALLOWED_LANGUAGE_AUTHORITIES,
                f"language {name}: invalid authority {authority!r}")
        require(not language.get("acceptance_authority") or authority == "canonical",
                f"language {name}: supporting language cannot have acceptance authority")

    canonical = [x for x in data.get("language", []) if x.get("authority") == "canonical"]
    require(len(canonical) == 1, "exactly one canonical language is required")
    require("kernel" in canonical[0].get("roles", []),
            "canonical language must own the kernel role")


def validate_governance(data: dict, repository_id: str, root: Path) -> None:
    governance = data.get("governance")
    if repository_id == GOVERNANCE_REPOSITORY:
        require(governance is None, "governance source repository must not pin itself")
        return

    require(governance and governance.get("repository") == GOVERNANCE_REPOSITORY,
            f"[governance] must pin repository {GOVERNANCE_REPOSITORY}")
    require(re.fullmatch(r"[0-9a-f]{40}", governance.get("revision", "")),
            "governance.revision must be a 40-hex commit")
    digests = governance.get("sha256", {})
    require(set(digests) == set(VENDORED),
            f"governance.sha256 must cover exactly the vendored file set {sorted(VENDORED)}")
    for rel, digest in sorted(digests.items()):
        require((root / rel).is_file(), f"missing vendored governance file: {rel}")
        require(sha256(root / rel) == digest,
                f"vendored governance file digest mismatch (local edit?): {rel}")


def validate_workspaces(repository_id: str, root: Path) -> None:
    workspace = root / "pixi.toml"
    if workspace.is_file():
        expected = repository_id.split("/", 1)[1]
        name = tomllib.loads(workspace.read_text(encoding="utf-8")).get("workspace", {}).get("name")
        require(name == expected, f"pixi workspace identity disagrees with estate.toml: expected {expected!r}")

    polyglot = root / "polyglot.manifest.toml"
    if polyglot.is_file():
        pdata = tomllib.loads(polyglot.read_text(encoding="utf-8"))
        require(pdata.get("repository") == repository_id,
                "polyglot.manifest.toml repository disagrees with estate.toml")
        require(pdata.get("estate", {}).get("manifest") == "estate.toml",
                "polyglot.manifest.toml must link to estate.toml")
        if (root / "oracles/julia").exists():
            require("Julia" in pdata.get("authority", {}).get("supporting_languages", []),
                    "Julia oracle lane exists but polyglot supporting_languages omits Julia")


def validate(data: dict, root: Path = ROOT) -> None:
    repository_id = validate_identity(data)
    validate_principles(data)
    validate_planes(data, root)
    validate_languages(data)
    for required in ENTRYPOINTS:
        require((root / required).is_file(), f"missing architecture entrypoint: {required}")
    validate_governance(data, repository_id, root)
    validate_workspaces(repository_id, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    root = parser.parse_args(argv).root.resolve()
    try:
        validate(load(root / "estate.toml"), root)
    except (AssertionError, tomllib.TOMLDecodeError) as exc:
        print(f"estate-layout audit failed: {exc}", file=sys.stderr)
        return 1
    print("estate-layout audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
