#!/usr/bin/env python3
"""Estate CI impact-policy v1 validator and *advisory* change-impact planner.

The policy is treated as untrusted data. This module never executes test
commands or emits acceptance, proof, or deployment verdicts. The source repo
must enforce execution and final required checks separately.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SCHEMA = "estate-ci-impact-v1"
ID = re.compile(r"[a-z][a-z0-9_-]*")
REPO = re.compile(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+")
SHA = re.compile(r"[0-9a-f]{40}")
ALLOWED_MODES = {"always", "affected"}


class PolicyError(ValueError):
    """Fail-closed policy or source-provenance error."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


def keys(data: object, required: set[str], optional: set[str], at: str) -> dict:
    require(isinstance(data, dict), f"{at}: expected TOML table")
    missing = required - data.keys()
    extra = data.keys() - required - optional
    require(not missing, f"{at}: missing keys: {sorted(missing)}")
    require(not extra, f"{at}: unknown keys: {sorted(extra)}")
    return data


def name(value: object, where: str) -> str:
    require(isinstance(value, str) and ID.fullmatch(value) is not None,
            f"{where}: invalid identifier")
    return value


def patterns(value: object, where: str) -> list[str]:
    require(isinstance(value, list) and bool(value), f"{where}: nonempty list required")
    result = []
    for item in value:
        require(isinstance(item, str) and bool(item), f"{where}: invalid path pattern")
        prefix = item[:-3] if item.endswith("/**") else item
        require(
            prefix and not prefix.startswith("/") and "\\" not in prefix
            and all(part not in ("", ".", "..") for part in prefix.split("/"))
            and not any(c in prefix for c in "*?[]{}\x00\r\n"),
            f"{where}: unsafe or unsupported pattern {item!r}",
        )
        result.append(item)
    require(len(result) == len(set(result)), f"{where}: duplicate patterns")
    return result


def strings(value: object, where: str, *, nonempty: bool = True) -> list[str]:
    require(isinstance(value, list) and (bool(value) or not nonempty),
            f"{where}: expected {'nonempty ' if nonempty else ''}list")
    require(all(isinstance(x, str) and bool(x) for x in value),
            f"{where}: nonempty strings required")
    require(len(set(value)) == len(value), f"{where}: duplicates")
    return value


def covered(path: str, pattern: str) -> bool:
    return path == pattern or (pattern.endswith("/**") and
                              (path == pattern[:-3] or path.startswith(pattern[:-3] + "/")))


def overlaps(a: str, b: str) -> bool:
    if a == b:
        return True
    if a.endswith("/**") and covered(b[:-3] if b.endswith("/**") else b, a):
        return True
    if b.endswith("/**") and covered(a[:-3] if a.endswith("/**") else a, b):
        return True
    return False


def validate(policy: dict, root: Path, *, require_entrypoints: bool = True) -> dict:
    root = root.resolve(strict=True)
    keys(policy, {"version", "schema", "repository", "selection", "component", "suite"}, set(), "policy")
    require(type(policy["version"]) is int and policy["version"] == 1, "unsupported policy version")
    require(policy["schema"] == SCHEMA, "unknown impact schema")
    require(isinstance(policy["repository"], str) and REPO.fullmatch(policy["repository"]) is not None,
            "invalid repository")
    estate_file = root / "ESTATE.toml"
    require(estate_file.is_file(), "missing ESTATE.toml")
    estate = tomllib.loads(estate_file.read_text(encoding="utf-8"))
    require(policy["repository"] == estate.get("repo", {}).get("slug"),
            "policy repository differs from ESTATE.toml")

    sel = keys(policy["selection"], {"unmapped", "full_on", "ignore"}, set(), "selection")
    require(sel["unmapped"] == "full", "unmapped paths must force full selection")
    full_on = patterns(sel["full_on"], "selection.full_on")
    ignore = patterns(sel["ignore"], "selection.ignore")
    for a in full_on:
        for b in ignore:
            require(not overlaps(a, b), f"full_on and ignore patterns overlap: {a}, {b}")

    components = {}
    ownership = []
    require(isinstance(policy["component"], list) and policy["component"], "component list required")
    for row in policy["component"]:
        keys(row, {"id", "paths", "depends_on"}, set(), "component")
        cid = name(row["id"], "component.id")
        require(cid not in components, f"duplicate component {cid}")
        own = patterns(row["paths"], f"{cid}.paths")
        deps = strings(row["depends_on"], f"{cid}.depends_on", nonempty=False)
        for pattern in own:
            for previous, owner in ownership:
                require(not overlaps(pattern, previous),
                        f"ambiguous path ownership: {pattern} ({cid}) and {previous} ({owner})")
            ownership.append((pattern, cid))
        components[cid] = deps
    for cid, deps in components.items():
        require(all(dep in components for dep in deps), f"{cid}: unknown dependency")
        require(cid not in deps, f"{cid}: self-dependency")

    visiting, visited = set(), set()
    def visit(cid: str) -> None:
        require(cid not in visiting, f"component dependency cycle at {cid}")
        if cid in visited:
            return
        visiting.add(cid)
        for dep in components[cid]:
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)
    for cid in components:
        visit(cid)

    suites = {}
    require(isinstance(policy["suite"], list) and policy["suite"], "suite list required")
    referenced = set()
    for row in policy["suite"]:
        keys(row, {"id", "mode", "components", "entrypoints"}, set(), "suite")
        sid = name(row["id"], "suite.id")
        require(sid not in suites, f"duplicate suite {sid}")
        require(row["mode"] in ALLOWED_MODES, f"{sid}: unknown mode")
        targets = strings(row["components"], f"{sid}.components")
        require(all(c in components for c in targets), f"{sid}: unknown component")
        referenced.update(targets)
        paths = patterns(row["entrypoints"], f"{sid}.entrypoints")
        require(all(not p.endswith("/**") for p in paths),
                f"{sid}: entrypoints must be exact files")
        if require_entrypoints:
            for target in paths:
                p = root / target
                require(p.is_file() and p.resolve().is_relative_to(root),
                        f"{sid}: missing or escaping entrypoint {target}")
        suites[sid] = row
    require(set(components) <= referenced, "component without an owning suite")
    require(any(s["mode"] == "always" for s in suites.values()),
            "at least one always-run suite is required")
    return {"components": components, "owners": ownership, "suites": suites}


def load(path: Path) -> dict:
    require(path.is_file(), f"missing policy {path}")
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _valid_path(path: str) -> bool:
    return bool(path) and not path.startswith("/") and "\\" not in path and (
        all(part not in ("", ".", "..") for part in path.split("/"))
        and not any(c in path for c in "\x00\r\n")
    )


def plan(policy: dict, model: dict, paths: list[str], *, force_full: bool = False) -> dict:
    require(isinstance(paths, list) and all(isinstance(p, str) and _valid_path(p) for p in paths),
            "invalid changed path")
    paths = sorted(set(paths))
    full_on = policy["selection"]["full_on"]
    ignore = policy["selection"]["ignore"]
    affected = set()
    unknown = []
    reasons = ["requested full verification"] if force_full else []
    for p in paths:
        if any(covered(p, pat) for pat in full_on):
            reasons.append(f"critical change: {p}")
            continue
        if any(covered(p, pat) for pat in ignore):
            continue
        owners = [cid for pat, cid in model["owners"] if covered(p, pat)]
        if len(owners) == 1:
            affected.add(owners[0])
        elif not owners:
            unknown.append(p)
        else:
            reasons.append(f"ambiguous ownership: {p}")
    if unknown:
        reasons.append("unmapped changed paths require full verification")
    closure = set(affected)
    while True:
        new = {c for c, deps in model["components"].items() if set(deps) & closure}
        if new <= closure:
            break
        closure.update(new)
    suites = model["suites"]
    full = bool(reasons)
    selected = sorted(suites) if full else sorted(sid for sid, spec in suites.items()
        if spec["mode"] == "always" or set(spec["components"]) & closure)
    skipped = [] if full else [
        {"suite": sid, "reason": "outside reverse dependency closure under validated policy"}
        for sid in sorted(suites) if sid not in selected
    ]
    return {
        "schema": SCHEMA, "decision": "full" if full else ("targeted" if closure else "preflight-only"),
        "changed_paths": paths, "direct_components": sorted(affected),
        "dependency_closure": sorted(model["components"]) if full else sorted(closure),
        "selected_suites": selected, "skipped_suites": skipped,
        "unmapped_paths": unknown, "reasons": reasons,
        "source_coverage": "local-only",
        "verdict": "selection-plan-only",
    }


def git_diff(root: Path, base: str, head: str) -> list[str]:
    require(isinstance(base, str) and SHA.fullmatch(base) is not None, "invalid comparison base SHA")
    require(isinstance(head, str) and SHA.fullmatch(head) is not None, "invalid tested SHA")
    def git(*args: str) -> bytes:
        try:
            return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise PolicyError(f"unavailable source revision or invalid git comparison: {args[0]}") from exc
    checked_out = git("rev-parse", "HEAD").decode().strip()
    require(checked_out == head, "tested SHA does not match checked-out HEAD")
    for sha in (base, head):
        require(git("cat-file", "-t", sha).strip() == b"commit", "comparison object is not a commit")
    output = git("diff", "--name-only", "--no-renames", "-z", f"{base}...{head}", "--")
    result = output.decode("utf-8", "strict").split("\x00")
    return [p for p in result if p]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=Path("policy/ci-impact.toml"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        path = (root / args.policy).resolve()
        require(path.is_relative_to(root), "policy path escapes repository")
        raw = path.read_bytes()
        policy = tomllib.loads(raw.decode("utf-8"))
        model = validate(policy, root)
        if args.check:
            require(not (args.paths or args.full or args.base or args.head or args.output),
                    "--check cannot be combined with planning")
            print(f"validated {policy['repository']} {SCHEMA}: "
                  f"{len(model['components'])} components, {len(model['suites'])} suites")
            return 0
        require(not (args.paths and (args.base or args.head)),
                "explicit --path and git comparison are mutually exclusive")
        require(args.full or args.paths is not None or (args.base and args.head),
                "planning requires --path, --full, or both --base and --head")
        paths = [] if args.full and not (args.base and args.head) else (
            git_diff(root, args.base, args.head) if args.base and args.head else (args.paths or [])
        )
        decision = plan(policy, model, paths, force_full=args.full)
        decision["repository"] = policy["repository"]
        decision["policy_digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        decision["tested_revision"] = args.head if args.head else None
        decision["comparison_base"] = args.base if args.base else None
        receipt = json.dumps(decision, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(receipt, encoding="utf-8")
        print(receipt, end="")
        return 0
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, PolicyError) as exc:
        print(f"CI IMPACT POLICY BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
