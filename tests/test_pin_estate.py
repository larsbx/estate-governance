from __future__ import annotations

import hashlib
import re
import tomllib

import pytest
from pathlib import Path

import audit_estate_layout as audit
import pin_estate

ROOT = Path(__file__).resolve().parents[1]
REV = "a" * 40

MANIFEST = f'''version = 2

[repo]
id = "consumer"

[[dep]]
id = "estate-governance"
rev = "{"0" * 40}"
pin = "sha256:{"0" * 64}"

[[dep]]                       # vendored packages
id = "finite-math-kernels"
pin = "sha256:{"0" * 64}"   # pinned by digest

[[plane]]
id = "kernel"
'''

VENDORED = f'''[[package]]
name = "finite_exact"
repository = "larsbx/finite-math-kernels"
commit = "{"c" * 40}"
root = "vendor/mojo"

[package.files]
"finite_exact/rat_q.mojo" = "{"d" * 64}"
'''


def consumer(tmp_path: Path) -> Path:
    target = tmp_path / "vendor/mojo/finite_exact/rat_q.mojo"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"vendored exact arithmetic")
    vendored = VENDORED.replace("d" * 64, audit.sha256(target))
    (tmp_path / "ESTATE.toml").write_text(MANIFEST, encoding="utf-8")
    (tmp_path / "vendored.toml").write_text(vendored, encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def committed_audit(monkeypatch):
    monkeypatch.setattr(pin_estate, "audit_at_revision", lambda revision: b"committed audit")


def deps(root: Path) -> dict:
    return {d["id"]: d for d in tomllib.loads((root / "ESTATE.toml").read_text(encoding="utf-8"))["dep"]}


def test_pin_sets_the_governance_rev_and_audit_digest_and_the_vendored_digests(tmp_path: Path):
    root = consumer(tmp_path)
    pin_estate.pin(root, REV)
    d = deps(root)
    audit_digest = hashlib.sha256(b"committed audit").hexdigest()
    assert d["estate-governance"] == {"id": "estate-governance", "rev": REV, "pin": "sha256:" + audit_digest}
    assert d["finite-math-kernels"]["pin"] == "sha256:" + audit.vendored_digest(root, "larsbx/finite-math-kernels")


def test_pin_keeps_everything_else_and_is_idempotent(tmp_path: Path):
    root = consumer(tmp_path)
    pin_estate.pin(root, REV)
    once = (root / "ESTATE.toml").read_text(encoding="utf-8")
    assert "# vendored packages" in once and "# pinned by digest" in once and '[[plane]]\nid = "kernel"' in once
    pin_estate.pin(root, REV)
    assert (root / "ESTATE.toml").read_text(encoding="utf-8") == once


def test_check_reports_drift_and_writes_nothing(tmp_path: Path):
    root = consumer(tmp_path)
    assert pin_estate.main([str(root), "--revision", REV, "--check"]) == 1
    assert (root / "ESTATE.toml").read_text(encoding="utf-8") == MANIFEST
    pin_estate.pin(root, REV)
    assert pin_estate.main([str(root), "--revision", REV, "--check"]) == 0


def test_a_missing_governance_dep_is_an_error(tmp_path: Path):
    (tmp_path / "ESTATE.toml").write_text("version = 2\n", encoding="utf-8")
    try:
        pin_estate.pin(tmp_path, REV)
    except SystemExit as exc:
        assert "estate-governance" in str(exc)
    else:
        raise AssertionError("expected a failure")


def test_revision_hashes_committed_audit_not_worktree(tmp_path, monkeypatch):
    root = consumer(tmp_path)
    monkeypatch.setattr(pin_estate, "audit_at_revision", lambda rev: b"committed audit")
    values = pin_estate.wanted(root, REV)
    assert values[pin_estate.GOVERNANCE_ID]["pin"] == "sha256:" + hashlib.sha256(b"committed audit").hexdigest()


@pytest.mark.parametrize("field", ["rev", "pin"])
def test_check_rejects_missing_required_governance_field(tmp_path, monkeypatch, field):
    root = consumer(tmp_path)
    revision = "a" * 40
    monkeypatch.setattr(pin_estate, "audit_at_revision", lambda rev: b"audit")
    manifest = root / pin_estate.MANIFEST
    text = manifest.read_text(encoding="utf-8")
    text = re.sub(rf"^{field}\s*=.*\n", "", text, flags=re.MULTILINE)
    manifest.write_text(text, encoding="utf-8")
    assert pin_estate.main([str(root), "--revision", revision, "--check"]) == 1
