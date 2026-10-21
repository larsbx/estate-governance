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

REV = re.compile(r"[0-9a-f]{40}")
BLOB = re.compile(r"[0-9a-f]{40}")
INV = re.compile(r"INV-[A-Z0-9][A-Z0-9-]*")
STAGES = ("candidate", "seeded", "incubating", "stable", "frozen", "archived")
BANDS = ("EXPLORE", "STANDARD", "HARDENED", "LAW")
CLASSES = {"kernel", "substrate", "platform", "app", "research", "corpus", "meta"}


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: object, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path = REGISTRY) -> dict:
    require(path.is_file(), f"missing estate registry: {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


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


def validate(data: dict) -> dict:
    require(data.get("version") == 1, "registry version must be 1")
    require(data.get("schema") == "estate-registry-v1", "unknown estate registry schema")

    governance_source_commit = data.get("governance_source_commit", "")
    required_audit_revision = data.get("required_audit_revision", "")
    require(
        isinstance(governance_source_commit, str) and REV.fullmatch(governance_source_commit),
        "governance_source_commit must be a 40-hex commit",
    )
    require(
        isinstance(required_audit_revision, str) and REV.fullmatch(required_audit_revision),
        "required_audit_revision must be a 40-hex commit",
    )

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
        canonical_language = member.get("canonical_language")
        acceptance_authority = member.get("acceptance_authority")
        require(repo_class in CLASSES, f"{member_id}: unknown class {repo_class!r}")
        require(type(layer) is int, f"{member_id}: layer must be an integer")
        require(band in BANDS, f"{member_id}: unknown band {band!r}")
        require(stage in STAGES, f"{member_id}: unknown stage {stage!r}")
        require(
            isinstance(canonical_language, str) and canonical_language,
            f"{member_id}: canonical_language is required",
        )
        require(
            type(acceptance_authority) is bool,
            f"{member_id}: acceptance_authority must be Boolean",
        )
        require(member.get("ci_gate") is True, f"{member_id}: estate CI gate is not recorded as active")

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

        inv = _string_list(member, "inv")
        for prefix in inv:
            require(INV.fullmatch(prefix), f"{member_id}: malformed INV prefix {prefix!r}")
            inv_rows.append((prefix, member_id))

        exports = _string_list(member, "exports")
        export_rows.extend((name, member_id) for name in exports)

        deps = _string_list(member, "deps")
        conforms = _string_list(member, "conforms")
        namespaces = _string_list(member, "claim_namespaces")
        namespace_rows.extend((name, member_id) for name in namespaces)

        workspace = member.get("workspace", "single")
        require(workspace in {"single", "multi_program"}, f"{member_id}: invalid workspace {workspace!r}")
        if workspace == "single":
            require(not namespaces, f"{member_id}: single workspace cannot declare claim_namespaces")
        else:
            require(len(namespaces) >= 2, f"{member_id}: multi_program needs at least two claim namespaces")

        by_id[member_id] = {
            **member,
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

    return {
        "members": len(by_id),
        "governance_source_commit": governance_source_commit,
        "required_audit_revision": required_audit_revision,
        "code_edges": sum(len(v) for v in graph.values()),
        "conformance_edges": sum(len(m["conforms"]) for m in by_id.values()),
        "exports": len(export_rows),
        "inv_prefixes": len(inv_rows),
        "claim_namespaces": len(namespace_rows),
        "accepting_members": sum(bool(m["acceptance_authority"]) for m in by_id.values()),
        "nonaccepting_members": sum(not bool(m["acceptance_authority"]) for m in by_id.values()),
        "stages": {stage: sum(m["stage"] == stage for m in by_id.values()) for stage in STAGES},
    }


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
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
