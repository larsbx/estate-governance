#!/usr/bin/env python3
"""Acquire immutable source observations and check registry provenance/freshness.

Use --fetch with a new --sources directory for a live observation. Without
--fetch, replay that directory's receipt and Git objects; this is not a new
observation of GitHub. No member code is checked out or executed.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import snapshot_registry as snap

POLICY = "manifest-current-v1"
REF = "refs/heads/estate-observed"
RECEIPT = "observation.json"
ID = re.compile(r"[a-z0-9][a-z0-9-]*")
OID = re.compile(r"[0-9a-f]{40}")


class FreshnessError(ValueError):
    pass


def members(data: dict) -> list[dict]:
    rows = data.get("member")
    if not isinstance(rows, list) or not rows:
        raise FreshnessError("registry has no members")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise FreshnessError("invalid registry member")
        member_id = row.get("id", "")
        if not isinstance(member_id, str) or not ID.fullmatch(member_id):
            raise FreshnessError(f"unsafe member id: {member_id!r}")
        if member_id in seen or row.get("slug") != f"larsbx/{member_id}":
            raise FreshnessError(f"{member_id}: duplicate member or invalid GitHub slug")
        seen.add(member_id)
        for field in ("source_commit", "manifest_blob"):
            if not isinstance(row.get(field), str) or not OID.fullmatch(row[field]):
                raise FreshnessError(f"{member_id}: invalid {field}")
    if snap.GOVERNANCE_ID not in seen:
        raise FreshnessError("registry must include estate-governance")
    return rows


def describe_error(exc: Exception) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        return (exc.stderr or str(exc)).strip()
    return str(exc)


def acquire_member(member: dict, sources: Path, governance: Path,
                   governance_revision: str = "HEAD") -> dict:
    member_id, slug = member["id"], member["slug"]
    repo = sources / member_id
    snap.git(sources, "init", "--bare", str(repo))
    if member_id == snap.GOVERNANCE_ID:
        # The tested commit, including a PR merge commit, is the self observation.
        # It is deliberately not the mutable remote main and not the worktree.
        head = snap.git(governance, "rev-parse", "--verify",
                        f"{governance_revision}^{{commit}}").strip()
        snap.git(repo, "fetch", "--no-tags", "--no-recurse-submodules",
                 str(governance.resolve()), f"{head}:{REF}")
        selected_ref = "tested HEAD"
    else:
        url = f"https://github.com/{slug}.git"
        snap.git(repo, "remote", "add", "origin", url)
        snap.git(repo, "config", "remote.origin.promisor", "true")
        snap.git(repo, "config", "remote.origin.partialclonefilter", "blob:none")
        # Full commit ancestry, lazy blobs. No shallow history, cache, tag, fork,
        # alternate branch, or fallback to the registry's old commit.
        snap.git(repo, "fetch", "--no-tags", "--no-recurse-submodules", "--filter=blob:none",
                 "origin", f"+refs/heads/main:{REF}")
        head = snap.git(repo, "rev-parse", "--verify", f"{REF}^{{commit}}").strip()
        selected_ref = "refs/heads/main"
    # Materialize precisely the objects consumed by the checker while the fetch
    # step has network access. Missing source commits/manifests are fatal.
    pinned = snap.snapshot(repo, member["source_commit"])
    snap.snapshot(repo, head)
    if member_id != snap.GOVERNANCE_ID:
        # The receipt replays locally; missing objects must not trigger a later
        # lazy network fetch that changes the meaning/availability of evidence.
        snap.git(repo, "config", "remote.origin.promisor", "false")
    return {
        "id": member_id, "slug": slug, "ref": selected_ref, "commit": head,
        "source_commit": member["source_commit"],
        "source_inputs": snap.inputs(repo, pinned["source_commit"]),
        "observed_inputs": snap.inputs(repo, head),
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def acquire(data: dict, sources: Path, governance: Path,
            governance_revision: str = "HEAD") -> dict:
    rows = members(data)
    # Exclusive creation makes a failed fetch incapable of reusing old sources.
    sources.mkdir(parents=True, exist_ok=False)
    receipt = {"version": 1, "policy": POLICY, "complete": False, "member": [], "errors": []}

    def fetch(row):
        try:
            result = acquire_member(row, sources, governance, governance_revision)
            print(f"captured {row['slug']} at {result['commit']}", flush=True)
            return result, None
        except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
            return None, f"{row['slug']}: {describe_error(exc)}"

    with ThreadPoolExecutor(max_workers=4) as pool:
        for result, error in pool.map(fetch, rows):
            if error:
                receipt["errors"].append(error)
            else:
                receipt["member"].append(result)
    receipt["complete"] = not receipt["errors"]
    (sources / RECEIPT).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def check(data: dict, sources: Path, receipt: dict,
          tested_revision: str | None = None) -> list[str]:
    rows = members(data)
    if (not isinstance(receipt, dict) or type(receipt.get("version")) is not int
            or receipt.get("version") != 1 or receipt.get("policy") != POLICY
            or receipt.get("complete") is not True or receipt.get("errors") != []):
        raise FreshnessError("source observation is incomplete or has an unsupported policy")
    observations = receipt.get("member", [])
    if (not isinstance(observations, list)
            or any(not isinstance(row, dict) or not isinstance(row.get("id"), str)
                   for row in observations)):
        raise FreshnessError("invalid observation membership")
    by_id = {row["id"]: row for row in observations}
    if len(by_id) != len(observations) or set(by_id) != {row["id"] for row in rows}:
        raise FreshnessError("observation membership must exactly match the registry")
    errors = []
    governance = next(row for row in rows if row["id"] == snap.GOVERNANCE_ID)
    if data.get("governance_source_commit") != governance["source_commit"]:
        errors.append("governance_source_commit disagrees with estate-governance row")
    for member in rows:
        member_id = member["id"]
        observation = by_id[member_id]
        repo = sources / member_id
        try:
            if not (repo / "HEAD").is_file() or not (repo / "objects").is_dir():
                raise FreshnessError("missing captured bare repository")
            head = observation["commit"]
            timestamp = observation.get("observed_at")
            if not isinstance(timestamp, str) or datetime.fromisoformat(timestamp).utcoffset() != timezone.utc.utcoffset(None):
                raise FreshnessError("missing or invalid UTC observation time")
            if (member_id == snap.GOVERNANCE_ID and tested_revision is not None
                    and head != tested_revision):
                raise FreshnessError("governance observation disagrees with tested revision")
            expected_ref = "tested HEAD" if member_id == snap.GOVERNANCE_ID else "refs/heads/main"
            if (observation["slug"] != member["slug"] or observation["ref"] != expected_ref
                    or not isinstance(head, str) or not OID.fullmatch(head)):
                raise FreshnessError("observation identity/ref/commit disagrees with policy")
            if snap.git(repo, "rev-parse", "--verify", f"{REF}^{{commit}}").strip() != head:
                raise FreshnessError("observed Git revision disagrees with receipt")
            # Pin changes require a new acquisition, even if the old repository
            # happens to contain the new commit already.
            if observation["source_commit"] != member["source_commit"]:
                raise FreshnessError("source revision disagrees with receipt; acquire again")
            if member["source_commit"] != head:
                snap.git(repo, "merge-base", "--is-ancestor", member["source_commit"], head)
            pinned = snap.snapshot(repo, member["source_commit"])
            latest = snap.snapshot(repo, head)
            for prefix, commit in (("source", member["source_commit"]), ("observed", head)):
                if snap.inputs(repo, commit) != observation[f"{prefix}_inputs"]:
                    raise FreshnessError(f"{prefix} Git input provenance disagrees with receipt")
            if pinned != member:
                fields = sorted(k for k in pinned.keys() | member.keys() if pinned.get(k) != member.get(k))
                raise FreshnessError("recorded entry does not reproduce at source_commit: " + ", ".join(fields))
            # source_commit denotes a real reproducible snapshot, not necessarily
            # the newest code commit. Manifest bytes and all projected facts must
            # still match the captured head. This also solves self-reference.
            drift = sorted(k for k in latest.keys() | member.keys()
                           if k != "source_commit" and latest.get(k) != member.get(k))
            if drift:
                raise FreshnessError(f"stale against {head}: " + ", ".join(drift))
        except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
            errors.append(f"{member_id}: {describe_error(exc)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True, help="new capture directory, or one to replay")
    parser.add_argument("--registry", type=Path, default=snap.REGISTRY)
    parser.add_argument("--governance", type=Path, default=snap.ROOT, help="full-history tested checkout")
    parser.add_argument("--registry-revision", help="read registry AND self observation from this exact Git commit")
    parser.add_argument("--fetch", action="store_true", help="capture live sources into a NEW directory")
    args = parser.parse_args(argv)
    try:
        if args.registry_revision and not OID.fullmatch(args.registry_revision):
            raise FreshnessError("registry revision must be a full immutable commit ID")
        data = tomllib.loads(snap.git(args.governance, "show",
                                     f"{args.registry_revision}:policy/estate-registry.toml")
                             if args.registry_revision else args.registry.read_text(encoding="utf-8"))
        receipt = (acquire(data, args.sources, args.governance, args.registry_revision or "HEAD") if args.fetch else
                   json.loads((args.sources / RECEIPT).read_text(encoding="utf-8")))
        if not isinstance(receipt, dict):
            raise FreshnessError("invalid source observation")
        errors = (receipt.get("errors") or ["source observation is incomplete"]
                  if receipt.get("complete") is not True else
                  check(data, args.sources, receipt, args.registry_revision))
        if errors:
            for error in errors:
                print(f"registry freshness failed: {error}", file=sys.stderr)
            return 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"registry freshness failed: {describe_error(exc)}", file=sys.stderr)
        return 1
    print(f"registry freshness passed: {len(data['member'])} members ({POLICY}, captured observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
