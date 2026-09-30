#!/usr/bin/env python3
"""Validate a repository's estate manifest, ESTATE.toml (estate-repository-v2).

The manifest carries SPEC_estate v0.1 §3 (identity, class, layer, band,
stage, origin, code and conformance edges, exports) and this template's
in-repository layout (authority planes, languages, migration queue).

Canonical and only copy: larsbx/estate-governance, kernel/audit_estate_layout.py.
Consumers do not vendor it (SPEC_estate §5). Their CI checks this repository
out at the commit their ESTATE.toml pins as a [[dep]] and runs

    python .estate/kernel/audit_estate_layout.py --root .

The audit then refuses to pass unless its own bytes hash to that pin, so a
consumer is always judged by exactly the audit it declared.

This audit checks one manifest against one tree. The estate-wide checks that
need every manifest at once (SPEC_estate EA1-EA7: acyclicity, layering across
edges, name uniqueness, the stage ledger) are not implemented here.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "ESTATE.toml"
TEMPLATE = "estate-repository-v2"

GOVERNANCE_REPOSITORY = "larsbx/estate-governance"
GOVERNANCE_ID = GOVERNANCE_REPOSITORY.split("/")[1]

#: SPEC_estate §1: class -> (default layer, default band). The meta-repo sits outside the layering.
CLASSES: dict[str, tuple[int, str]] = {
    "kernel": (0, "HARDENED"),
    "substrate": (1, "STANDARD"),
    "platform": (2, "STANDARD"),
    "app": (3, "STANDARD"),
    "research": (3, "EXPLORE"),
    "corpus": (3, "EXPLORE"),
}
META = "meta"
BANDS = ("EXPLORE", "STANDARD", "HARDENED", "LAW")
STAGES = ("candidate", "seeded", "incubating", "stable", "frozen", "archived")

PIN = re.compile(r"sha256:[0-9a-f]{64}|tag:[A-Za-z0-9._/-]+")
REV = re.compile(r"[0-9a-f]{40}")
DECISION = re.compile(r"DR-\d{4}")

#: Top-level directories outside every plane: hidden ones (including the .estate
#: checkout of this repository) and build artifacts (Python bytecode, setuptools
#: metadata, the standard build/ and dist/ outputs, and the coverage/ report
#: directory, which Julia coverage tooling writes at the root).
UNTRACKED = re.compile(r"\..*|__pycache__|.*\.egg-info|build|dist|coverage")

CONTRACT = "docs/architecture/estate-repository-template-v2.md"

ALLOWED_PLANE_AUTHORITIES = frozenset({
    "program_collection",
    "shared_component_collection",
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
    path = path or ROOT / MANIFEST
    require(path.is_file(), f"missing estate manifest: {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def vendored_digest(root: Path, repository: str) -> str:
    """Validate and hash vendored metadata together with the listed file contents."""
    packages = tomllib.loads((root / "vendored.toml").read_text(encoding="utf-8")).get("package", [])
    rows = []
    for package in packages:
        if package.get("repository") != repository:
            continue
        package_root = root / str(package.get("root", ""))
        files = package.get("files", {})
        require(isinstance(files, dict) and files, f"vendored package {package.get('name')}: files are required")
        bound_files = {}
        for rel, recorded in sorted(files.items()):
            candidate = (package_root / rel).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                fail(f"vendored package {package.get('name')}: file escapes repository: {rel}")
            require(candidate.is_file(), f"vendored package {package.get('name')}: missing listed file {rel}")
            actual = sha256(candidate)
            require(actual == recorded,
                    f"vendored package {package.get('name')}: content hash mismatch for {rel}")
            bound_files[rel] = {"recorded": recorded, "actual": actual}
        rows.append({
            "name": package.get("name"),
            "commit": package.get("commit"),
            "root": package.get("root"),
            "files": bound_files,
        })
    rows.sort(key=lambda row: row["name"])
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_repo(data: dict) -> dict:
    require(data.get("version") == 2, "ESTATE.toml version must be 2")
    require(data.get("template") == TEMPLATE, f"ESTATE.toml template must be {TEMPLATE}")
    repo = data.get("repo", {})
    rid, slug, cls = repo.get("id", ""), repo.get("slug", ""), repo.get("class")
    require(re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid), "repo.id must be a lowercase repository name")
    require(re.fullmatch(r"[^/\s]+/[^/\s]+", slug), "repo.slug must be OWNER/REPOSITORY")
    require(slug.split("/")[1] == rid, "repo.slug must name repo.id")
    require(cls in CLASSES or cls == META, f"repo.class must be one of {sorted([*CLASSES, META])}")
    require(repo.get("band") in BANDS, f"repo.band must be one of {list(BANDS)}")
    require(repo.get("stage") in STAGES, f"repo.stage must be one of {list(STAGES)}")
    require("override" not in repo or DECISION.fullmatch(str(repo["override"])),
            "repo.override must name a decision record (DR-nnnn)")
    if cls == META:
        require(slug == GOVERNANCE_REPOSITORY, f"class meta is reserved for {GOVERNANCE_REPOSITORY}")
        require("layer" not in repo, "the estate meta-repo sits outside the layering: no layer")
    else:
        layer, band = CLASSES[cls]
        if "override" not in repo:
            require(repo.get("layer") == layer,
                    f"layer {repo.get('layer')} differs from the {cls} default {layer}; name a decision record in repo.override")
            require(repo["band"] == band,
                    f"band {repo['band']} differs from the {cls} default {band}; name a decision record in repo.override")
        require(repo.get("layer") in (0, 1, 2, 3), "repo.layer must be 0, 1, 2 or 3")
    for prefix in repo.get("inv", []):
        require(re.fullmatch(r"INV-[A-Z][A-Z0-9]*", prefix), f"INV family prefix must look like INV-XX: {prefix!r}")
    return repo


def validate_origin(data: dict, repo: dict) -> None:
    origin = data.get("origin", {})
    require(origin.get("decided_by") in ("stated", "proposed"), "origin.decided_by must be stated or proposed")
    if origin["decided_by"] == "proposed":
        require(repo["stage"] == "candidate", "decided_by = proposed caps the repo at candidate (SPEC_estate §3)")
    suite = origin.get("genesis_suite")
    require(suite is None or suite == "green" or re.fullmatch(r"xfail:\S+", suite),
            "origin.genesis_suite must be green or xfail:<test ids>")
    require(all(re.fullmatch(r"https://\S+", c) for c in origin.get("chats", [])), "origin.chats must be https links")
    require(all(isinstance(a, dict) and a.get("path") and re.fullmatch(r"sha256:[0-9a-f]{64}", str(a.get("h", "")))
                for a in origin.get("artifacts", [])),
            "origin.artifacts entries need a path and a sha256 h")


def validate_edges(data: dict, repo: dict, root: Path) -> None:
    deps = data.get("dep", [])
    ids = [d.get("id") for d in deps]
    for dup in {i for i in ids if ids.count(i) > 1}:
        fail(f"duplicate dep: {dup}")
    for dep in deps:
        require(PIN.fullmatch(str(dep.get("pin", ""))),
                f"dep {dep.get('id')}: pin must be a content hash or signed tag (sha256:... or tag:...), never a floating ref")

    if repo["slug"] == GOVERNANCE_REPOSITORY:
        require(not deps, "the estate meta-repo imports nothing (SPEC_estate §11)")
    else:
        governance = next((d for d in deps if d.get("id") == GOVERNANCE_ID), None)
        require(governance, f"a consumer must depend on {GOVERNANCE_ID} ([[dep]] with rev and pin)")
        require(REV.fullmatch(str(governance.get("rev", ""))), f"dep {GOVERNANCE_ID}: rev must be a 40-hex commit")
        require(governance["pin"] == "sha256:" + sha256(Path(__file__)),
                f"dep {GOVERNANCE_ID}: pin does not match the running audit; check out the pinned rev")
        require(not (root / "tools" / "audit_estate_layout.py").exists(),
                "a vendored copy of the estate audit is forbidden (SPEC_estate §5); CI checks governance out")

    vendored = root / "vendored.toml"
    if vendored.is_file():
        packages = tomllib.loads(vendored.read_text(encoding="utf-8")).get("package", [])
        for source in sorted({p.get("repository") for p in packages}):
            dep = next((d for d in deps if d.get("id") == source.split("/")[1]), None)
            require(dep, f"vendors packages from {source} without a [[dep]]")
            require(dep["pin"] == "sha256:" + vendored_digest(root, source),
                    f"dep {dep['id']}: pin disagrees with vendored.toml")

    for edge in data.get("conform", []):
        require(edge.get("id"), "conform.id is required")
        require(edge.get("vectors"), f"conform {edge['id']}: vectors is required")

    names = data.get("exports", {}).get("names", [])
    for dup in {n for n in names if names.count(n) > 1}:
        fail(f"duplicate export: {dup}")



PROGRAM_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
CLAIM_NAMESPACE = re.compile(r"[A-Z][A-Z0-9]*")


def repository_relative_path(value: object, field: str, prefix: str) -> Path:
    require(isinstance(value, str) and value, f"{field} is required")
    candidate = Path(value)
    require(not candidate.is_absolute() and ".." not in candidate.parts,
            f"{field} must be a repository-relative path without '..'")
    require(candidate.parts and candidate.parts[0] == prefix,
            f"{field} must be below {prefix}/")
    return candidate


def validate_program_workspace(data: dict, root: Path) -> None:
    """Validate optional multi-program workspace boundaries.

    Branches remain change lines; durable mathematical concerns are declared as
    directory-rooted programs. Existing repositories default to single-program
    mode and remain valid without workspace metadata.
    """
    workspace = data.get("workspace", {})
    mode = workspace.get("mode", "single")
    require(mode in {"single", "multi_program"},
            "workspace.mode must be single or multi_program")

    programs = data.get("program", [])
    components = data.get("shared_component", [])
    if mode == "single":
        require(not programs and not components,
                "[[program]] and [[shared_component]] require workspace.mode = multi_program")
        return

    require(len(programs) >= 2, "a multi_program workspace requires at least two [[program]] entries")
    program_ids: set[str] = set()
    roots: set[str] = set()
    namespaces: set[str] = set()
    for program in programs:
        program_id = program.get("id", "")
        require(PROGRAM_ID.fullmatch(str(program_id)),
                f"program.id must be lowercase and stable: {program_id!r}")
        require(program_id not in program_ids, f"duplicate program id: {program_id}")
        program_ids.add(program_id)

        program_root = repository_relative_path(program.get("root"), f"program {program_id}: root", "programs")
        root_text = program_root.as_posix()
        require(root_text not in roots, f"duplicate program root: {root_text}")
        roots.add(root_text)
        require((root / program_root).is_dir(), f"program {program_id}: missing root {root_text}")

        manifest_name = program.get("manifest", "PROGRAM.toml")
        require(manifest_name == "PROGRAM.toml",
                f"program {program_id}: manifest must be PROGRAM.toml")
        manifest_path = root / program_root / manifest_name
        require(manifest_path.is_file(),
                f"program {program_id}: missing manifest {root_text}/{manifest_name}")
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        identity = manifest.get("program", {})
        require(identity.get("id") == program_id,
                f"program {program_id}: PROGRAM.toml identity disagrees with root manifest")

        namespace = program.get("claim_namespace", "")
        require(CLAIM_NAMESPACE.fullmatch(str(namespace)),
                f"program {program_id}: claim_namespace must be uppercase alphanumeric")
        require(namespace not in namespaces, f"duplicate program claim_namespace: {namespace}")
        namespaces.add(namespace)

        language = program.get("canonical_language", "")
        require(isinstance(language, str) and language,
                f"program {program_id}: canonical_language is required")

    component_ids: set[str] = set()
    for component in components:
        component_id = component.get("id", "")
        require(PROGRAM_ID.fullmatch(str(component_id)),
                f"shared_component.id must be lowercase and stable: {component_id!r}")
        require(component_id not in component_ids, f"duplicate shared_component id: {component_id}")
        component_ids.add(component_id)

        component_root = repository_relative_path(
            component.get("root"), f"shared_component {component_id}: root", "shared")
        root_text = component_root.as_posix()
        require(root_text not in roots, f"duplicate workspace root: {root_text}")
        roots.add(root_text)
        require((root / component_root).is_dir(),
                f"shared_component {component_id}: missing root {root_text}")

        consumers = component.get("consumers", [])
        require(isinstance(consumers, list) and consumers,
                f"shared_component {component_id}: consumers must be non-empty")
        unknown = sorted(set(consumers) - program_ids)
        require(not unknown,
                f"shared_component {component_id}: unknown consumers {unknown}")


def validate_principles(data: dict) -> None:
    principles = data.get("principles", {})
    require(principles.get("ordering") == ["authority", "domain", "language"],
            "principles.ordering must be authority, domain, language")
    require(principles.get("cross_language_disagreement") == "fail_closed",
            "cross-language disagreement must fail closed")
    require(principles.get("empty_silos") == "forbidden", "empty silos must be forbidden")


def validate_planes(data: dict, root: Path) -> None:
    require(data.get("layout", {}).get("status") in {"transitional", "canonical"},
            "layout.status must be transitional or canonical")
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

    if data["layout"]["status"] == "canonical":
        validate_canonical(data, root)


def validate_canonical(data: dict, root: Path) -> None:
    """Canonical: every plane maps its target (root-level files aside), and every
    top-level directory is some plane's target."""
    for plane in data["plane"]:
        current = plane.get("current", [])
        extras = [rel for rel in current if rel != plane["target"]]
        require(
            plane["target"] in current
            and not plane.get("current_globs")
            and all("/" not in rel and (root / rel).is_file() for rel in extras),
            f"canonical layout: plane {plane['id']} must map its target {plane['target']!r} "
            "plus only root-level files",
        )
    require(not data.get("migration", {}).get("next"), "canonical layout must have no pending migration")
    targets = {plane["target"] for plane in data["plane"]}
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and not UNTRACKED.fullmatch(entry.name):
            require(entry.name in targets,
                    f"canonical layout: top-level directory {entry.name!r} belongs to no plane")


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


def validate_workspaces(slug: str, root: Path) -> None:
    workspace = root / "pixi.toml"
    if workspace.is_file():
        expected = slug.split("/", 1)[1]
        name = tomllib.loads(workspace.read_text(encoding="utf-8")).get("workspace", {}).get("name")
        require(name == expected, f"pixi workspace identity disagrees with {MANIFEST}: expected {expected!r}")

    polyglot = root / "polyglot.manifest.toml"
    if polyglot.is_file():
        pdata = tomllib.loads(polyglot.read_text(encoding="utf-8"))
        require(pdata.get("repository") == slug, f"polyglot.manifest.toml repository disagrees with {MANIFEST}")
        require(pdata.get("estate", {}).get("manifest") == MANIFEST, f"polyglot.manifest.toml must link to {MANIFEST}")
        if (root / "oracles/julia").exists():
            require("Julia" in pdata.get("authority", {}).get("supporting_languages", []),
                    "Julia oracle lane exists but polyglot supporting_languages omits Julia")


def validate(data: dict, root: Path = ROOT) -> None:
    repo = validate_repo(data)
    validate_origin(data, repo)
    validate_principles(data)
    validate_program_workspace(data, root)
    validate_planes(data, root)
    validate_languages(data)
    entrypoints = ["ARCHITECTURE.md"] + ([CONTRACT] if repo["slug"] == GOVERNANCE_REPOSITORY else [])
    for required in entrypoints:
        require((root / required).is_file(), f"missing architecture entrypoint: {required}")
    validate_edges(data, repo, root)
    validate_workspaces(repo["slug"], root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    root = parser.parse_args(argv).root.resolve()
    try:
        validate(load(root / MANIFEST), root)
    except (AssertionError, tomllib.TOMLDecodeError) as exc:
        print(f"estate audit failed: {exc}", file=sys.stderr)
        return 1
    print("estate audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
