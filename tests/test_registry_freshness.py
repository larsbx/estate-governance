from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import zlib

import pytest

import check_registry_freshness as fresh
import snapshot_registry as snap


def commit(repo: Path, name: str) -> str:
    snap.git(repo, "add", ".")
    snap.git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "commit", "-m", name)
    return snap.git(repo, "rev-parse", "HEAD").strip()


def create_repo(parent: Path, member_id: str) -> Path:
    repo = parent / member_id
    repo.mkdir(parents=True)
    snap.git(repo, "init", "-b", "main")
    meta = member_id == "estate-governance"
    (repo / "ESTATE.toml").write_text(f'''
[repo]
id = "{member_id}"
slug = "larsbx/{member_id}"
class = "{'meta' if meta else 'research'}"
layer = {'-1' if meta else '3'}
band = "STANDARD"
stage = "candidate"
[origin]
decided_by = "proposed"
[[language]]
name = "Python"
authority = "canonical"
acceptance_authority = true
''', encoding="utf-8")
    workflow = repo / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("run: python kernel/audit_estate_layout.py\n", encoding="utf-8")
    commit(repo, "initial inputs")
    return repo


@pytest.fixture
def estate(tmp_path, monkeypatch):
    origins = {name: create_repo(tmp_path / "origins", name) for name in ("estate-governance", "demo")}
    rows = [snap.snapshot(repo, "HEAD") for repo in origins.values()]
    data = {"version": 1, "schema": "estate-registry-v1", "member": rows,
            "governance_source_commit": rows[0]["source_commit"],
            "required_audit_revision": "a" * 40}
    real_git = snap.git

    def local_git(repo, *args):
        # Only replace the transport URL; exercise the real fetch, history,
        # object reads, acquisition receipt and checker without network access.
        args = tuple(str(origins["demo"]) if arg == "https://github.com/larsbx/demo.git" else arg
                     for arg in args)
        return real_git(repo, *args)

    monkeypatch.setattr(snap, "git", local_git)
    return data, origins, tmp_path / "capture"


def capture(estate):
    data, origins, sources = estate
    receipt = fresh.acquire(data, sources, origins["estate-governance"])
    assert receipt["complete"], receipt["errors"]
    return data, origins, sources, receipt


def test_real_git_acquisition_and_replay_pass(estate):
    data, _, sources, receipt = capture(estate)
    assert fresh.check(data, sources, receipt) == []
    assert json.loads((sources / fresh.RECEIPT).read_text()) == receipt
    assert receipt["member"][1]["ref"] == "refs/heads/main"
    assert snap.git(sources / "demo", "config", "remote.origin.promisor").strip() == "false"


def test_unrelated_code_commit_does_not_force_snapshot_churn(estate):
    data, origins, _ = estate
    (origins["demo"] / "code.py").write_text("# unrelated code\n")
    newer = commit(origins["demo"], "unrelated code")
    data, _, sources, receipt = capture(estate)
    assert receipt["member"][1]["commit"] == newer != data["member"][1]["source_commit"]
    assert fresh.check(data, sources, receipt) == []


def test_manifest_byte_drift_fails_even_if_projection_unchanged(estate):
    _, origins, _ = estate
    manifest = origins["demo"] / "ESTATE.toml"
    manifest.write_text(manifest.read_text() + "\n# changed bytes\n")
    commit(origins["demo"], "manifest comment")
    data, _, sources, receipt = capture(estate)
    assert "manifest_blob" in "\n".join(fresh.check(data, sources, receipt))


def test_workflow_gate_removal_fails_without_manifest_change(estate):
    _, origins, _ = estate
    (origins["demo"] / ".github/workflows/ci.yml").write_text("run: pytest\n")
    commit(origins["demo"], "remove estate gate")
    data, _, sources, receipt = capture(estate)
    assert "ci_gate" in "\n".join(fresh.check(data, sources, receipt))


def test_governance_uses_tested_head_and_avoids_self_reference(estate):
    _, origins, _ = estate
    gov = origins["estate-governance"]
    snap.git(gov, "switch", "-c", "proposed-change")
    (gov / "registry.txt").write_text("a snapshot of the preceding commit")
    tested = commit(gov, "registry-only PR commit")
    data, _, sources, receipt = capture(estate)
    assert receipt["member"][0]["commit"] == tested
    assert receipt["member"][0]["ref"] == "tested HEAD"
    assert tested != snap.git(gov, "rev-parse", "main").strip()
    assert fresh.check(data, sources, receipt) == []


@pytest.mark.parametrize("field,value", [("class", "app"), ("manifest_blob", "f" * 40),
                                       ("ci_gate", False), ("extra", "not generated")])
def test_inconsistent_generated_entry_fails(estate, field, value):
    data, _, sources, receipt = capture(estate)
    data["member"][1][field] = value
    assert "does not reproduce" in "\n".join(fresh.check(data, sources, receipt))


def test_pin_change_requires_new_acquisition(estate):
    data, _, sources, receipt = capture(estate)
    data["member"][1]["source_commit"] = "f" * 40
    assert "source revision disagrees" in "\n".join(fresh.check(data, sources, receipt))


def test_unavailable_source_commit_fails_acquisition(estate):
    data, origins, sources = estate
    data["member"][1]["source_commit"] = "f" * 40
    receipt = fresh.acquire(data, sources, origins["estate-governance"])
    assert receipt["complete"] is False and receipt["errors"]
    with pytest.raises(fresh.FreshnessError, match="incomplete"):
        fresh.check(data, sources, receipt)


def test_commit_outside_observed_ancestry_is_rejected(estate):
    data, _, sources, receipt = capture(estate)
    repo = sources / "demo"
    tree = snap.git(repo, "rev-parse", f"{fresh.REF}^{{tree}}").strip()
    # A real Git commit with identical inputs but no parent on the observed main.
    orphan = snap.git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                      "commit-tree", tree, "-m", "unrelated root").strip()
    data["member"][1]["source_commit"] = orphan
    receipt["member"][1]["source_commit"] = orphan
    assert fresh.check(data, sources, receipt)


def test_missing_repository_fails_replay(estate):
    data, _, sources, receipt = capture(estate)
    shutil.rmtree(sources / "demo")
    assert "demo" in "\n".join(fresh.check(data, sources, receipt))


def test_unavailable_remote_never_reuses_old_snapshot(estate):
    data, origins, sources = estate
    shutil.rmtree(origins["demo"])
    receipt = fresh.acquire(data, sources, origins["estate-governance"])
    assert receipt["complete"] is False
    assert "larsbx/demo" in "\n".join(receipt["errors"])


@pytest.mark.parametrize("missing", ["manifest", "main"])
def test_missing_manifest_or_branch_fails_acquisition(estate, missing):
    data, origins, sources = estate
    repo = origins["demo"]
    if missing == "manifest":
        (repo / "ESTATE.toml").unlink()
        commit(repo, "missing manifest")
    else:
        snap.git(repo, "branch", "-m", "other")
    receipt = fresh.acquire(data, sources, origins["estate-governance"])
    assert receipt["complete"] is False and receipt["errors"]


def test_missing_object_fails_without_lazy_network_fetch(estate):
    data, _, sources, receipt = capture(estate)
    repo = sources / "demo"
    blob = data["member"][1]["manifest_blob"]
    # Turn this tiny fixture's packed objects into loose objects so removing one
    # immutable input works independently of Git's pack layout.
    objects = snap.git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)")
    for line in objects.splitlines():
        oid, kind = line.split()
        content = subprocess.run(["git", "-C", str(repo), "cat-file", kind, oid],
                                 capture_output=True, check=True).stdout
        target = repo / "objects" / oid[:2] / oid[2:]
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(zlib.compress(f"{kind} {len(content)}\0".encode() + content))
    shutil.rmtree(repo / "objects/pack")
    (repo / "objects" / blob[:2] / blob[2:]).unlink()
    snap.git(repo, "config", "remote.origin.url", "/nonexistent/remote")
    assert fresh.check(data, sources, receipt)


def test_changed_captured_revision_is_rejected(estate):
    data, _, sources, receipt = capture(estate)
    (sources / "demo/refs/heads/estate-observed").write_text("f" * 40 + "\n")
    assert fresh.check(data, sources, receipt)


@pytest.mark.parametrize("receipt", [[], {"version": True}, {"version": 1, "policy": fresh.POLICY,
                                                        "complete": True, "member": [None]}])
def test_malformed_receipt_fails_closed(estate, receipt):
    data, _, sources = estate
    with pytest.raises(fresh.FreshnessError):
        fresh.check(data, sources, receipt)


@pytest.mark.parametrize("field,value", [("commit", "f" * 40), ("slug", "larsbx/other"),
                                       ("ref", "refs/heads/other"),
                                       ("source_inputs", {}), ("observed_inputs", {})])
def test_altered_observation_provenance_is_rejected(estate, field, value):
    data, _, sources, receipt = capture(estate)
    receipt["member"][1][field] = value
    assert fresh.check(data, sources, receipt)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra"])
def test_observation_requires_exact_membership(estate, mutation):
    data, _, sources, receipt = capture(estate)
    if mutation == "missing":
        receipt["member"].pop()
    else:
        extra = copy.deepcopy(receipt["member"][1])
        if mutation == "extra":
            extra["id"] = "extra"
        receipt["member"].append(extra)
    with pytest.raises(fresh.FreshnessError, match="membership"):
        fresh.check(data, sources, receipt)


def test_header_source_revision_cannot_disagree(estate):
    data, _, sources, receipt = capture(estate)
    data["governance_source_commit"] = "f" * 40
    assert "governance_source_commit" in "\n".join(fresh.check(data, sources, receipt))


def test_existing_capture_directory_cannot_be_reused(estate):
    data, origins, sources, _ = capture(estate)
    with pytest.raises(FileExistsError):
        fresh.acquire(data, sources, origins["estate-governance"])


def test_snapshot_rejects_wrong_repository_identity(estate, tmp_path):
    data, _, sources, _ = capture(estate)
    # Sources must never be silently selected by a colliding directory name.
    shutil.rmtree(sources / "demo")
    shutil.copytree(sources / "estate-governance", sources / "demo")
    registry = tmp_path / "registry.toml"
    registry.write_text(snap.render({k: data[k] for k in ("governance_source_commit", "required_audit_revision")},
                                   data["member"]))
    with pytest.raises(ValueError, match="identity"):
        snap.build(sources, fresh.REF, registry)


def test_cli_returns_failure_and_does_not_rewrite_registry(estate, tmp_path, capsys):
    data, _, sources, _ = capture(estate)
    data["member"][1]["class"] = "app"
    registry = tmp_path / "registry.toml"
    text = snap.render({k: data[k] for k in ("governance_source_commit", "required_audit_revision")}, data["member"])
    registry.write_text(text)
    assert fresh.main(["--sources", str(sources), "--registry", str(registry)]) == 1
    assert "does not reproduce" in capsys.readouterr().err
    assert registry.read_text() == text
