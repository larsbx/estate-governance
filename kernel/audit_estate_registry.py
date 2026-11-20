#!/usr/bin/env python3
"""Validate estate-wide invariants over policy/estate-registry.toml.

The repository-local audit validates one ESTATE.toml against one tree. This
checker validates invariants that only become meaningful when multiple estate
members are considered together.

Conformance edges are intentionally *not* part of the code-dependency DAG:
independent implementations may replay one another's vectors reciprocally.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "policy" / "estate-registry.toml"
DECISIONS = ROOT / "docs" / "decisions"

REV = re.compile(r"[0-9a-f]{40}")
BLOB = re.compile(r"[0-9a-f]{40}")
INV = re.compile(r"INV-[A-Z0-9][A-Z0-9-]*")
DECISION = re.compile(r"DR-\d{4}")
ACCEPTED = re.compile(r"^- \*\*Status:\*\* accepted\s*$", re.M)
STAGES = ("candidate", "seeded", "incubating", "stable", "frozen", "archived")
BANDS = ("EXPLORE", "STANDARD", "HARDENED", "LAW")
CLASSES = {"kernel", "substrate", "platform", "app", "research", "corpus", "meta"}
REGISTRY_SCHEMAS = {1: "estate-registry-v1", 2: "estate-registry-v2"}
MANIFEST_TEMPLATES = {2: "estate-repository-v2", 3: "estate-repository-v3"}
BOUNDARY_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
FORMAL_TOOLCHAINS = {
    "lean": r"leanprover/lean4:(?:v\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?|nightly-\d{4}-\d{2}-\d{2})",
    "quint": r"@informalsystems/quint@\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?",
}
FORMAL_FIELDS = (
    "formalization_scope", "formalization_gate", "implementation_paths",
    "lean_sources", "lean_toolchain", "lean_obligations",
    "quint_sources", "quint_toolchain", "quint_obligations",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: object, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path = REGISTRY) -> dict:
    require(path.is_file(), f"missing estate registry: {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def registry_version(data: dict) -> int:
    version = data.get("version")
    require(type(version) is int and version in REGISTRY_SCHEMAS,
            "registry version must be 1 or 2")
    require(data.get("schema") == REGISTRY_SCHEMAS[version], "unknown estate registry schema")
    return version


def _declared_path(value: object, label: str) -> None:
    require(isinstance(value, str) and value and not value.startswith("/")
            and "\\" not in value and not any(c in value for c in "\x00\r\n")
            and all(part not in ("", ".", "..") for part in value.split("/")),
            f"{label} must be a relative declared source path")


def _declaration_list(value: object, label: str) -> list[str]:
    require(isinstance(value, list) and value
            and all(isinstance(item, str) and item and item.strip() == item for item in value),
            f"{label} must be a nonempty string list")
    require(len(value) == len(set(value)), f"{label} must not contain duplicates")
    return value


def validate_member_contract(member: dict, version: int) -> tuple[int, str]:
    """Validate declarations only; neither registry version verifies execution evidence."""
    member_id = member.get("id", "<unknown>")
    if version == 1:
        manifest_version = member.get("manifest_version", 2)
        template = member.get("template", MANIFEST_TEMPLATES[2])
        require(type(manifest_version) is int and manifest_version == 2
                and template == MANIFEST_TEMPLATES[2],
                f"{member_id}: v3 manifests require estate-registry-v2")
        require("formalization_status" not in member,
                f"{member_id}: formalization declarations require estate-registry-v2")
    else:
        manifest_version = member.get("manifest_version")
        require(type(manifest_version) is int and manifest_version in MANIFEST_TEMPLATES,
                f"{member_id}: unsupported manifest_version")
        template = member.get("template")
        require(template == MANIFEST_TEMPLATES[manifest_version],
                f"{member_id}: manifest version and template disagree")
        require(member.get("formalization_status") == "not_evaluated",
                f"{member_id}: registry declarations must mark formalization not_evaluated")

    require(type(member.get("acceptance_authority")) is bool,
            f"{member_id}: acceptance_authority must be Boolean")
    if manifest_version == 2:
        language = member.get("canonical_language")
        require(isinstance(language, str) and language,
                f"{member_id}: canonical_language is required for historical v2 manifests")
        require(not any(field in member for field in FORMAL_FIELDS) and "boundaries" not in member,
                f"{member_id}: v2 rows cannot claim v3 boundary or formal declarations")
        return manifest_version, template

    require("canonical_language" not in member,
            f"{member_id}: v3 authority must not be derived from canonical_language")
    boundaries = member.get("boundaries")
    require(isinstance(boundaries, list), f"{member_id}: v3 boundaries must be a list")
    require(bool(boundaries) == member["acceptance_authority"],
            f"{member_id}: named boundary presence must agree with acceptance_authority")
    identifiers = set()
    for boundary in boundaries:
        require(isinstance(boundary, dict) and set(boundary) == {"id", "implementation", "contract"},
                f"{member_id}: malformed boundary declaration")
        identifier = boundary["id"]
        require(isinstance(identifier, str) and BOUNDARY_ID.fullmatch(identifier),
                f"{member_id}: boundary id must be lowercase and stable")
        require(identifier not in identifiers, f"{member_id}: duplicate boundary id")
        identifiers.add(identifier)
        _declared_path(boundary["contract"], f"{member_id}: boundary {identifier}.contract")
        for path in _declaration_list(boundary["implementation"],
                                      f"{member_id}: boundary {identifier}.implementation"):
            _declared_path(path, f"{member_id}: boundary {identifier}.implementation")
    for field in ("formalization_scope", "formalization_gate"):
        _declared_path(member.get(field), f"{member_id}: {field}")
    for field in ("implementation_paths", "lean_sources", "quint_sources"):
        paths = _declaration_list(member.get(field), f"{member_id}: {field}")
        for path in paths:
            _declared_path(path, f"{member_id}: {field}")
            if field in ("lean_sources", "quint_sources"):
                suffix = ".lean" if field == "lean_sources" else ".qnt"
                require(Path(path).suffix == suffix, f"{member_id}: {field} must name {suffix} sources")
    for lane in ("lean", "quint"):
        toolchain = member.get(f"{lane}_toolchain")
        require(isinstance(toolchain, str) and re.fullmatch(FORMAL_TOOLCHAINS[lane], toolchain),
                f"{member_id}: {lane}_toolchain must declare an exact version")
        obligations = _declaration_list(member.get(f"{lane}_obligations"),
                                         f"{member_id}: {lane}_obligations")
        require(all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*", name) for name in obligations),
                f"{member_id}: {lane}_obligations must name declarations or properties")
    return manifest_version, template


def accepted_decisions(directory: Path = DECISIONS) -> set[str]:
    """IDs of decision records in `directory` whose status is accepted."""
    return {
        path.name[:7]
        for path in directory.glob("DR-[0-9][0-9][0-9][0-9]-*.md")
        if ACCEPTED.search(path.read_text(encoding="utf-8"))
    }


def _string_list(member: dict, key: str) -> list[str]:
    value = member.get(key, [])
    require(
        isinstance(value, list) and all(isinstance(x, str) and x for x in value),
        f"{member.get('id', '<unknown>')}: {key} must be a list of nonempty strings",
    )
    return value


def _assert_unique(rows: list[tuple[str, str]], label: str) -> None:
    owners: dict[str, str] = {}
    for value, owner in rows:
        previous = owners.get(value)
        require(previous is None, f"duplicate {label} {value!r}: {previous} and {owner}")
        owners[value] = owner


def _dependency_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    white, gray, black = 0, 1, 2
    state = {node: white for node in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = gray
        stack.append(node)
        for dep in graph[node]:
            if state[dep] == white:
                cycle = visit(dep)
                if cycle:
                    return cycle
            elif state[dep] == gray:
                start = stack.index(dep)
                return stack[start:] + [dep]
        stack.pop()
        state[node] = black
        return None

    for node in graph:
        if state[node] == white:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def validate(data: dict, decisions: set[str] | None = None) -> dict:
    decisions = accepted_decisions() if decisions is None else decisions
    version = registry_version(data)

    governance_source_commit = data.get("governance_source_commit", "")
    require(
        isinstance(governance_source_commit, str) and REV.fullmatch(governance_source_commit),
        "governance_source_commit must be a 40-hex commit",
    )
    if version == 1:
        required_audit_revision = data.get("required_audit_revision", "")
        require(isinstance(required_audit_revision, str) and REV.fullmatch(required_audit_revision),
                "required_audit_revision must be a 40-hex commit")
        require("required_audit_revisions" not in data,
                "per-template audit revisions require estate-registry-v2")
        required_audit_revisions = {MANIFEST_TEMPLATES[2]: required_audit_revision}
    else:
        require("required_audit_revision" not in data,
                "estate-registry-v2 requires per-template audit revisions")
        required_audit_revisions = data.get("required_audit_revisions")
        require(isinstance(required_audit_revisions, dict) and required_audit_revisions,
                "required_audit_revisions must be a nonempty per-template table")
        for template, revision in required_audit_revisions.items():
            require(template in MANIFEST_TEMPLATES.values(), "unknown auditor manifest template")
            require(isinstance(revision, str) and REV.fullmatch(revision),
                    f"{template}: required audit revision must be 40-hex")

    members = data.get("member")
    require(isinstance(members, list) and members, "registry needs at least one [[member]]")

    by_id: dict[str, dict] = {}
    slug_rows: list[tuple[str, str]] = []
    export_rows: list[tuple[str, str]] = []
    inv_rows: list[tuple[str, str]] = []
    namespace_rows: list[tuple[str, str]] = []

    for member in members:
        require(isinstance(member, dict), "each member must be a table")
        member_id = member.get("id", "")
        slug = member.get("slug", "")
        require(isinstance(member_id, str) and member_id, "member.id is required")
        require(member_id not in by_id, f"duplicate member id: {member_id}")
        require(slug == f"larsbx/{member_id}", f"{member_id}: slug disagrees with id")

        source_commit = member.get("source_commit", "")
        manifest_blob = member.get("manifest_blob", "")
        require(
            isinstance(source_commit, str) and REV.fullmatch(source_commit),
            f"{member_id}: source_commit must be 40-hex",
        )
        require(
            isinstance(manifest_blob, str) and BLOB.fullmatch(manifest_blob),
            f"{member_id}: manifest_blob must be 40-hex",
        )

        repo_class = member.get("class")
        layer = member.get("layer")
        band = member.get("band")
        stage = member.get("stage")
        require(repo_class in CLASSES, f"{member_id}: unknown class {repo_class!r}")
        require(type(layer) is int, f"{member_id}: layer must be an integer")
        require(band in BANDS, f"{member_id}: unknown band {band!r}")
        require(stage in STAGES, f"{member_id}: unknown stage {stage!r}")
        manifest_version, template = validate_member_contract(member, version)
        require(template in required_audit_revisions,
                f"{member_id}: no required audit revision for {template}")
        required_audit_revision = required_audit_revisions[template]
        require(member.get("ci_gate") is True, f"{member_id}: estate CI gate is not recorded as active")

        decided_by = member.get("decided_by")
        require(decided_by in ("stated", "proposed"), f"{member_id}: decided_by must be stated or proposed")
        if decided_by == "stated":
            decision = member.get("decision", "")
            require(isinstance(decision, str) and DECISION.fullmatch(decision),
                    f"{member_id}: a stated position must name a decision record (DR-nnnn)")
            require(decision in decisions,
                    f"{member_id}: no accepted decision record {decision} in docs/decisions")
        else:
            require(stage == "candidate", f"{member_id}: decided_by = proposed caps the stage at candidate")

        if repo_class == "meta":
            require(member_id == "estate-governance", "only estate-governance may be class meta")
            require(layer == -1, "estate-governance meta layer must be -1 in the registry")
            require("governance_rev" not in member, "estate-governance must not depend on itself")
        else:
            require(layer >= 0, f"{member_id}: non-meta layer must be nonnegative")
            require(
                member.get("governance_rev") == required_audit_revision,
                f"{member_id}: governance audit revision is stale or disagrees with registry "
                f"({member.get('governance_rev')!r} != {required_audit_revision})",
            )

        # An archived member keeps its history but releases its names.
        claims_names = stage != "archived"
        inv = _string_list(member, "inv")
        for prefix in inv:
            require(INV.fullmatch(prefix), f"{member_id}: malformed INV prefix {prefix!r}")
        exports = _string_list(member, "exports")
        deps = _string_list(member, "deps")
        conforms = _string_list(member, "conforms")
        namespaces = _string_list(member, "claim_namespaces")
        if claims_names:
            inv_rows.extend((prefix, member_id) for prefix in inv)
            export_rows.extend((name, member_id) for name in exports)
            namespace_rows.extend((name, member_id) for name in namespaces)

        workspace = member.get("workspace", "single")
        require(workspace in {"single", "multi_program"}, f"{member_id}: invalid workspace {workspace!r}")
        if workspace == "single":
            require(not namespaces, f"{member_id}: single workspace cannot declare claim_namespaces")
        else:
            require(len(namespaces) >= 2, f"{member_id}: multi_program needs at least two claim namespaces")

        by_id[member_id] = {
            **member,
            "manifest_version": manifest_version,
            "template": template,
            "deps": deps,
            "conforms": conforms,
            "exports": exports,
            "inv": inv,
            "claim_namespaces": namespaces,
        }
        slug_rows.append((slug, member_id))

    require("estate-governance" in by_id, "registry must contain estate-governance")
    require(
        by_id["estate-governance"]["source_commit"] == governance_source_commit,
        "governance_source_commit must equal estate-governance source_commit",
    )

    _assert_unique(slug_rows, "repository slug")
    _assert_unique(export_rows, "export")
    _assert_unique(inv_rows, "INV prefix")
    _assert_unique(namespace_rows, "claim namespace")

    graph: dict[str, list[str]] = {member_id: [] for member_id in by_id}
    for member_id, member in by_id.items():
        for dep in member["deps"]:
            require(dep in by_id, f"{member_id}: dependency names unregistered member {dep!r}")
            require(dep != member_id, f"{member_id}: self dependency")
            graph[member_id].append(dep)
            source_layer = member["layer"]
            target_layer = by_id[dep]["layer"]
            if target_layer >= 0:
                require(
                    target_layer <= source_layer,
                    f"{member_id}: layer {source_layer} depends upward on "
                    f"{dep} at layer {target_layer}",
                )

        for target in member["conforms"]:
            require(target in by_id, f"{member_id}: conformance edge names unregistered member {target!r}")
            require(target != member_id, f"{member_id}: self conformance edge")

    cycle = _dependency_cycle(graph)
    require(cycle is None, "code dependency cycle: " + " -> ".join(cycle or []))

    summary = {
        "members": len(by_id),
        "governance_source_commit": governance_source_commit,
        "code_edges": sum(len(v) for v in graph.values()),
        "conformance_edges": sum(len(m["conforms"]) for m in by_id.values()),
        "exports": len(export_rows),
        "inv_prefixes": len(inv_rows),
        "claim_namespaces": len(namespace_rows),
        "accepting_members": sum(bool(m["acceptance_authority"]) for m in by_id.values()),
        "nonaccepting_members": sum(not bool(m["acceptance_authority"]) for m in by_id.values()),
        "stages": {stage: sum(m["stage"] == stage for m in by_id.values()) for stage in STAGES},
    }
    if version == 1:
        summary["required_audit_revision"] = required_audit_revisions[MANIFEST_TEMPLATES[2]]
    else:
        summary["required_audit_revisions"] = required_audit_revisions
        summary["manifest_versions"] = {
            str(v): sum(m["manifest_version"] == v for m in by_id.values())
            for v in MANIFEST_TEMPLATES
        }
        summary["formalization_evidence"] = "not_evaluated"
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        summary = validate(load(args.registry))
    except (AssertionError, tomllib.TOMLDecodeError) as exc:
        print(f"estate-wide audit failed: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "estate-wide audit passed: "
            f"{summary['members']} members, "
            f"{summary['code_edges']} code edges, "
            f"{summary['conformance_edges']} conformance edges"
            + ("; declarations only, formalization not evaluated"
               if summary.get("formalization_evidence") == "not_evaluated" else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
