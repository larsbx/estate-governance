#!/usr/bin/env python3
"""Trusted, environment-approved acquisition entry point; never run PR code.

The workflow pins this file and its imports to an independently reviewed commit.
Only candidate registry bytes and Git objects cross that trust boundary.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import check_registry_freshness as fresh
import snapshot_registry as snap

AUTH_SCHEME = "github-app-installation-contents-read-v1"


def source_slugs(data: dict) -> list[str]:
    return sorted(row["slug"] for row in fresh.members(data)
                  if row["id"] != snap.GOVERNANCE_ID)


def candidate_data(repo: Path, revision: str, trusted: dict) -> dict:
    if not fresh.OID.fullmatch(revision):
        raise fresh.FreshnessError("candidate must be a full immutable commit ID")
    data = tomllib.loads(snap.git(repo, "show", f"{revision}:policy/estate-registry.toml"))
    # A PR cannot expand credential scope or remove a source from the evidence
    # requirement. Membership changes need a new reviewed acquisition pin.
    if source_slugs(data) != source_slugs(trusted):
        raise fresh.FreshnessError("candidate membership differs from the trusted acquisition scope")
    return data


def prepare_candidate(repo: Path, revision: str, pull_request: int, trusted: dict) -> list[str]:
    if not fresh.OID.fullmatch(revision) or pull_request < 0:
        raise fresh.FreshnessError("invalid immutable candidate or pull request number")
    # Read an exact ref from the fixed governance origin, never a PR-supplied URL.
    # Fetching into a bare ref does not check out hooks, workflows or executables.
    source = f"refs/pull/{pull_request}/head" if pull_request else revision
    target = "refs/estate/candidate"
    snap.git(repo, "fetch", "--no-tags", "--no-recurse-submodules",
             "https://github.com/larsbx/estate-governance.git", f"+{source}:{target}")
    if snap.git(repo, "rev-parse", "--verify", f"{target}^{{commit}}").strip() != revision:
        raise fresh.FreshnessError("candidate ref moved; run again for the new immutable revision")
    candidate_data(repo, revision, trusted)
    return source_slugs(trusted)


def validate_installation_scope(token: str, slugs: list[str]) -> None:
    if not token or any(c.isspace() for c in token):
        raise fresh.FreshnessError("CONFIGURATION: a nonempty installation token is required")
    # This endpoint requires installation authentication. A PAT, invalid token,
    # unavailable installation or incomplete selection cannot pass as anonymous.
    request = Request("https://api.github.com/installation/repositories?per_page=100", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "estate-registry-freshness",
    })
    try:
        with urlopen(request, timeout=30) as response:
            # Do not follow pagination: this scope is deliberately bounded below
            # 100 repositories. Unexpected/excess scope is also a failure.
            data = json.load(response)
        repositories = data["repositories"]
        actual = [row["full_name"] for row in repositories]
        valid_scope = (type(data.get("total_count")) is int
                       and data["total_count"] == len(slugs) and sorted(actual) == slugs)
    except HTTPError as exc:
        raise fresh.FreshnessError(f"CONFIGURATION: installation authentication/access failed (HTTP {exc.code})") from None
    except (URLError, OSError, ValueError, KeyError, TypeError):
        raise fresh.FreshnessError("CONFIGURATION: installation scope could not be verified") from None
    if not valid_scope:
        raise fresh.FreshnessError("CONFIGURATION: installation repository scope must exactly match trusted members")


def git_environment(token: str, slugs: list[str]) -> dict[str, str]:
    """No token in argv, URLs, config files, artifacts, helpers or Git traces."""
    if not token or any(c.isspace() for c in token):
        raise fresh.FreshnessError("CONFIGURATION: a nonempty installation token is required")
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_") and key not in {
               "ESTATE_SOURCE_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "CURL_VERBOSE"}}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
                "ESTATE_AUTHENTICATED_ACQUISITION": "1"})
    settings = [("credential.helper", ""), ("credential.interactive", "never"),
                ("http.followRedirects", "false"), ("core.hooksPath", os.devnull),
                ("protocol.allow", "never"), ("protocol.https.allow", "always"),
                ("protocol.file.allow", "always")]
    encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    for slug in slugs:
        if not isinstance(slug, str) or not slug.startswith("larsbx/") or not fresh.ID.fullmatch(slug[7:]):
            raise fresh.FreshnessError("unsafe authenticated source slug")
        settings.append((f"http.https://github.com/{slug}.git.extraheader",
                         f"AUTHORIZATION: basic {encoded}"))
    for index, (key, value) in enumerate(settings):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    env["GIT_CONFIG_COUNT"] = str(len(settings))
    return env


@contextmanager
def authenticated_git(token: str, slugs: list[str]):
    # Acquisition's worker threads inherit this one controlled environment;
    # restore it after all have joined. No other code executes concurrently.
    before = dict(os.environ)
    controlled = git_environment(token, slugs)
    os.environ.clear()
    os.environ.update(controlled)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(before)


def save_receipt(path: Path, receipt: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--pull-request", type=int, default=0)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = {"version": 1, "policy": fresh.POLICY, "complete": False,
               "member": [], "tested_revision": args.candidate,
               "errors": ["CONFIGURATION: authenticated source acquisition has not completed"]}
    save_receipt(args.receipt, receipt)
    try:
        trusted = tomllib.loads(snap.REGISTRY.read_text(encoding="utf-8"))
        if args.command == "prepare":
            slugs = prepare_candidate(snap.ROOT, args.candidate, args.pull_request, trusted)
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
                output.write("repositories=" + ",".join(slug.split("/")[1] for slug in slugs) + "\n")
            return 0  # Preparation is not the acceptance result.
        if args.sources is None:
            raise fresh.FreshnessError("new --sources directory required for authenticated verification")
        data = candidate_data(snap.ROOT, args.candidate, trusted)
        slugs = source_slugs(trusted)
        token = os.environ.pop("ESTATE_SOURCE_TOKEN", "")
        validate_installation_scope(token, slugs)
        with authenticated_git(token, slugs):
            receipt = fresh.acquire(data, args.sources, snap.ROOT, args.candidate)
            receipt["tested_revision"] = args.candidate
            receipt["authentication"] = {"scheme": AUTH_SCHEME, "repositories": slugs}
            errors = (fresh.check(data, args.sources, receipt, args.candidate)
                      if receipt["complete"] is True else receipt["errors"])
        receipt["validation"] = {"passed": not errors, "errors": errors}
        save_receipt(args.receipt, receipt)
        if errors:
            for error in errors:
                print(f"registry freshness failed: {error}", file=sys.stderr)
            return 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        # Transport stderr is deliberately suppressed by snapshot_registry.git
        # during authenticated acquisition. API error bodies are never copied.
        receipt["complete"] = False
        receipt["errors"] = [fresh.describe_error(exc)]
        save_receipt(args.receipt, receipt)
        print(f"registry freshness failed: {receipt['errors'][0]}", file=sys.stderr)
        return 1
    print(f"registry freshness passed: {len(data['member'])} members, authenticated, at {args.candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
