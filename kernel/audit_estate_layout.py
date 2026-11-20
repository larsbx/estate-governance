#!/usr/bin/env python3
"""Validate a repository's estate manifest (v3, with explicit legacy v2 replay).

The manifest carries SPEC_estate v0.1 §3 (identity, class, layer, band,
stage, origin, code and conformance edges, exports) and this template's
in-repository boundaries, formalization declarations and optional layout.
V2 retains its historical language rules. V3 never derives authority from a
programming language and requires both Lean and Quint formalization declarations.
This is a static manifest audit: the declared formal gate must also execute.

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
TEMPLATE = "estate-repository-v3"
TEMPLATES = {2: "estate-repository-v2", 3: TEMPLATE}

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

CONTRACTS = {version: f"docs/architecture/estate-repository-template-v{version}.md"
             for version in TEMPLATES}

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
    version = data.get("version")
    require(type(version) is int and version in TEMPLATES,
            "ESTATE.toml version must be 2 (legacy) or 3")
    template = TEMPLATES[version]
    require(data.get("template") == template, f"ESTATE.toml template must be {template}")
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
    require(len(candidate.parts) >= 2 and candidate.parts[0] == prefix,
            f"{field} must name a child below {prefix}/")
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
    if data["version"] == 2:
        planes = data.get("plane", [])
        program_plane = next((p for p in planes if p.get("target") == "programs"), None)
        require(program_plane and program_plane.get("authority") == "program_collection",
                "a multi_program workspace requires a programs plane with program_collection authority")
        if components:
            shared_plane = next((p for p in planes if p.get("target") == "shared"), None)
            require(shared_plane and shared_plane.get("authority") == "shared_component_collection",
                    "shared components require a shared plane with shared_component_collection authority")

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
        if data["version"] == 3:
            require((root / program_root).resolve().is_relative_to(root.resolve()),
                    f"program {program_id}: root escapes repository through a symlink")

        manifest_name = program.get("manifest", "PROGRAM.toml")
        require(manifest_name == "PROGRAM.toml",
                f"program {program_id}: manifest must be PROGRAM.toml")
        manifest_path = root / program_root / manifest_name
        require(manifest_path.is_file(),
                f"program {program_id}: missing manifest {root_text}/{manifest_name}")
        if data["version"] == 3:
            require(manifest_path.resolve().is_relative_to((root / program_root).resolve()),
                    f"program {program_id}: child manifest escapes its program root")
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        identity = manifest.get("program", {})
        require(identity.get("id") == program_id,
                f"program {program_id}: PROGRAM.toml identity disagrees with root manifest")

        namespace = program.get("claim_namespace", "")
        require(CLAIM_NAMESPACE.fullmatch(str(namespace)),
                f"program {program_id}: claim_namespace must be uppercase alphanumeric")
        require(namespace not in namespaces, f"duplicate program claim_namespace: {namespace}")
        namespaces.add(namespace)

        if data["version"] == 2:
            language = program.get("canonical_language", "")
            require(isinstance(language, str) and language,
                    f"program {program_id}: canonical_language is required")

    component_ids: set[str] = set()
    for component in components:
        component_id = component.get("id", "")
        require(PROGRAM_ID.fullmatch(str(component_id)),
                f"shared_component.id must be lowercase and stable: {component_id!r}")
        require(component_id not in component_ids, f"duplicate shared_component id: {component_id}")
        require(component_id not in program_ids,
                f"workspace id is reused by a program and shared_component: {component_id}")
        component_ids.add(component_id)

        component_root = repository_relative_path(
            component.get("root"), f"shared_component {component_id}: root", "shared")
        root_text = component_root.as_posix()
        require(root_text not in roots, f"duplicate workspace root: {root_text}")
        roots.add(root_text)
        require((root / component_root).is_dir(),
                f"shared_component {component_id}: missing root {root_text}")
        if data["version"] == 3:
            require((root / component_root).resolve().is_relative_to(root.resolve()),
                    f"shared_component {component_id}: root escapes repository through a symlink")

        consumers = component.get("consumers", [])
        require(isinstance(consumers, list) and consumers,
                f"shared_component {component_id}: consumers must be non-empty")
        unknown = sorted(set(consumers) - program_ids)
        require(not unknown,
                f"shared_component {component_id}: unknown consumers {unknown}")


def validate_principles(data: dict) -> None:
    principles = data.get("principles", {})
    if data["version"] == 2:
        require(principles.get("ordering") == ["authority", "domain", "language"],
                "principles.ordering must be authority, domain, language")
        require(principles.get("cross_language_disagreement") == "fail_closed",
                "cross-language disagreement must fail closed")
    else:
        require(principles.get("ordering") == ["authority", "domain"],
                "v3 principles.ordering must be authority, domain")
        require(principles.get("disagreement") == "fail_closed", "disagreement must fail closed")
        for field, expected in (("generated_surfaces", "derived_only"),
                                ("vendor_code", "non_local"),
                                ("experimental_code", "non_authoritative")):
            require(principles.get(field) == expected, f"principles.{field} must be {expected}")
    require(principles.get("empty_silos") == "forbidden", "empty silos must be forbidden")


def validate_planes(data: dict, root: Path) -> None:
    if data["version"] == 3:
        require(isinstance(data.get("plane", []), list)
                and all(isinstance(plane, dict) for plane in data.get("plane", [])),
                "v3 plane inventory must be an array of tables")
        require(isinstance(data.get("layout", {}), dict), "v3 layout must be a table")
        if not data.get("plane"):
            require(not data.get("layout"), "v3 layout claims require an explicit plane inventory")
            return
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

    for mandatory in (("kernel", "policy") if data["version"] == 2 else ()):
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
        # Canonical ownership of the kernel does not itself grant acceptance
        # authority. Require an explicit choice; supporting entries may omit
        # the field (false), but every supplied value must be a TOML boolean.
        if authority == "canonical" or "acceptance_authority" in language:
            require(isinstance(language.get("acceptance_authority"), bool),
                    f"language {name}: acceptance_authority must be an explicit boolean")
        require(not language.get("acceptance_authority") or authority == "canonical",
                f"language {name}: supporting language cannot have acceptance authority")

    canonical = [x for x in data.get("language", []) if x.get("authority") == "canonical"]
    require(len(canonical) == 1, "exactly one canonical language is required")
    require("kernel" in canonical[0].get("roles", []),
            "canonical language must own the kernel role")
    # Exactly one canonical language, and zero or one acceptance authorities:
    # explicit false declares that the repository owns no acceptance/effect
    # boundary; true makes its canonical language the sole acceptance authority.


def validate_workspaces(slug: str, root: Path, version: int = 2) -> None:
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
        if version == 2 and (root / "oracles/julia").exists():
            require("Julia" in pdata.get("authority", {}).get("supporting_languages", []),
                    "Julia oracle lane exists but polyglot supporting_languages omits Julia")


def declared_file(root: Path, value: object, field: str, suffix: str | None = None) -> Path:
    """Resolve an owned contract input without following a path outside the repository."""
    require(isinstance(value, str) and value and not any(c in value for c in ("\\", "\0", "\n", "\r")),
            f"{field} must be a repository-relative file path")
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == value,
            f"{field} must be a normalized repository-relative file path")
    candidate = root / path
    require(candidate.resolve().is_relative_to(root.resolve()), f"{field} escapes the repository")
    require(not candidate.is_symlink() and candidate.is_file(), f"{field}: missing owned file {value}")
    require(candidate.stat().st_size > 0, f"{field}: empty file is not an artifact: {value}")
    if suffix is not None:
        require(path.suffix == suffix, f"{field} must name a {suffix} source")
    return candidate


def nonempty_strings(value: object, field: str) -> list[str]:
    require(isinstance(value, list) and value
            and all(isinstance(item, str) and item.strip() == item and item for item in value),
            f"{field} must be a nonempty string list")
    require(len(value) == len(set(value)), f"{field} must not contain duplicates")
    return value


def validate_authority(data: dict, root: Path) -> None:
    authority = data.get("authority", {})
    require(isinstance(authority, dict) and type(authority.get("acceptance_authority")) is bool,
            "authority.acceptance_authority must be an explicit boolean")
    boundaries = data.get("boundary", [])
    require(isinstance(boundaries, list) and all(isinstance(b, dict) for b in boundaries),
            "boundary must be an array of named boundaries")
    require(bool(boundaries) == authority["acceptance_authority"],
            "acceptance_authority must agree with the presence of named accepting boundaries")
    seen: set[str] = set()
    for boundary in boundaries:
        name = boundary.get("id", "")
        require(isinstance(name, str) and PROGRAM_ID.fullmatch(name), "boundary.id must be lowercase and stable")
        require(name not in seen, f"duplicate boundary: {name}")
        seen.add(name)
        declared_file(root, boundary.get("contract"), f"boundary {name}.contract")
        for path in nonempty_strings(boundary.get("implementation"), f"boundary {name}.implementation"):
            declared_file(root, path, f"boundary {name}.implementation")


def validate_formalization(data: dict, root: Path) -> None:
    """Check required declarations and artifacts; never pretend to execute or prove them."""
    formal = data.get("formalization", {})
    require(isinstance(formal, dict) and formal, "v3 requires Lean and Quint formalization")
    declared_file(root, formal.get("scope"), "formalization.scope")
    declared_file(root, formal.get("gate"), "formalization.gate")
    for path in nonempty_strings(formal.get("implementation_paths"), "formalization.implementation_paths"):
        declared_file(root, path, "formalization.implementation_paths")
    patterns = {
        "lean": (".lean", r"leanprover/lean4:(?:v\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?|nightly-\d{4}-\d{2}-\d{2})"),
        "quint": (".qnt", r"@informalsystems/quint@\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?"),
    }
    for lane, (suffix, toolchain_pattern) in patterns.items():
        entry = formal.get(lane, {})
        require(isinstance(entry, dict) and entry, f"formalization.{lane} is required")
        require(isinstance(entry.get("toolchain"), str)
                and re.fullmatch(toolchain_pattern, entry["toolchain"]),
                f"formalization.{lane}.toolchain must be an exact toolchain version")
        for path in nonempty_strings(entry.get("sources"), f"formalization.{lane}.sources"):
            declared_file(root, path, f"formalization.{lane}.sources", suffix)
        obligations = nonempty_strings(entry.get("obligations"), f"formalization.{lane}.obligations")
        require(all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", obligation) for obligation in obligations),
                f"formalization.{lane}.obligations must name declarations or properties")
        require("enabled" not in entry and "required" not in entry and "status" not in entry,
                f"formalization.{lane}: flags cannot disable or certify a required formal lane")
    require("required" not in formal and "enabled" not in formal and "status" not in formal,
            "formalization flags cannot disable or certify required execution")


def validate(data: dict, root: Path = ROOT) -> None:
    repo = validate_repo(data)
    validate_origin(data, repo)
    validate_principles(data)
    validate_program_workspace(data, root)
    validate_planes(data, root)
    if data["version"] == 2:
        validate_languages(data)
    else:
        validate_authority(data, root)
        validate_formalization(data, root)
    entrypoints = ["ARCHITECTURE.md"] + ([CONTRACTS[data["version"]]] if repo["slug"] == GOVERNANCE_REPOSITORY else [])
    for required in entrypoints:
        require((root / required).is_file(), f"missing architecture entrypoint: {required}")
    validate_edges(data, repo, root)
    validate_workspaces(repo["slug"], root, data["version"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    root = parser.parse_args(argv).root.resolve()
    try:
        data = load(root / MANIFEST)
        validate(data, root)
    except (AssertionError, tomllib.TOMLDecodeError, OSError, TypeError, ValueError, AttributeError) as exc:
        print(f"estate audit failed: {exc}", file=sys.stderr)
        return 1
    if data["version"] == 3:
        print("estate v3 manifest audit passed; Lean and Quint execution remains a separate required gate")
    else:
        print("estate audit passed (legacy v2; no v3 formalization compliance is established)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
