"""Failure controls for source-bound formal receipts, not substitutes for Lean/Quint."""
import json
from pathlib import Path

import pytest

import check_formal as formal


def seed_receipt(root: Path) -> Path:
    output = root / "formal/evidence"
    output.mkdir(parents=True)
    (output / "results.json").write_text('{"status":"passed"}')
    return output


def assert_failed(output: Path) -> dict:
    receipt = json.loads((output / "results.json").read_text())
    assert receipt["status"] == "failed"
    assert receipt["evidence_only"] is True
    assert receipt["domain_acceptance_authority"] is False
    assert receipt["implementation_correspondence"] == "unproved"
    return receipt


def test_missing_policy_replaces_stale_success(tmp_path):
    output = seed_receipt(tmp_path)
    assert formal.verify(tmp_path, output) == 1
    assert_failed(output)


def test_child_failure_replaces_stale_success(tmp_path, monkeypatch):
    output = seed_receipt(tmp_path)
    (tmp_path / "ESTATE.toml").write_text("version = 3\n")

    def fail(*_args):
        raise RuntimeError("required formal subprocess failed")

    monkeypatch.setattr(formal, "validate_declared_inputs", lambda *_args: ["ESTATE.toml"])
    monkeypatch.setattr(formal, "execute_checks", fail)
    assert formal.verify(tmp_path, output) == 1
    assert "required formal subprocess failed" in assert_failed(output)["failure"]


def test_changed_source_cannot_finish_with_success(tmp_path, monkeypatch):
    output = seed_receipt(tmp_path)
    (tmp_path / "ESTATE.toml").write_text("version = 3\n")
    model = tmp_path / "model.lean"
    model.write_text("original source")

    def change(*_args):
        model.write_text("changed during verification")

    monkeypatch.setattr(formal, "validate_declared_inputs", lambda *_args: ["ESTATE.toml"])
    monkeypatch.setattr(formal, "execute_checks", change)
    assert formal.verify(tmp_path, output) == 1
    assert assert_failed(output)["source_unchanged"] is False


def test_source_directory_cannot_be_excluded_as_output(tmp_path):
    with pytest.raises(ValueError, match="evidence must be"):
        formal.verify(tmp_path, tmp_path / "kernel")


@pytest.mark.parametrize("text", ["error: parsing failed", "error: typechecking failed", ""])
def test_arbitrary_nonzero_is_not_a_counterexample(tmp_path, text):
    with pytest.raises(RuntimeError, match="designated invariant failure"):
        formal.require_counterexample({"exit_code": 1}, text, tmp_path / "missing-trace.json")


def test_violation_message_without_witness_fails(tmp_path):
    trace = tmp_path / "trace.json"
    trace.write_text('{"states": []}')
    with pytest.raises(RuntimeError, match="two-state witness"):
        formal.require_counterexample({"exit_code": 1},
            "[violation] Found an issue\nerror: Invariant violated", trace)


@pytest.mark.parametrize("implementation", ["formal/evidence/implementation.py", "build/implementation.py"])
def test_declared_implementation_cannot_escape_source_digest(tmp_path, monkeypatch, implementation):
    spec = {"scope": "docs/scope.md", "gate": "tools/gate.py", "implementation_paths": [implementation],
            "lean": {"sources": ["formal/lean/model.lean"]},
            "quint": {"sources": ["formal/quint/model.qnt"]}}
    for name in formal.declared_inputs(spec):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("bound input\n")
    monkeypatch.setattr(formal, "configuration", lambda _root: spec)
    files, _digest = formal.source_snapshot(tmp_path)
    with pytest.raises(ValueError, match="declared input is excluded from the source digest"):
        formal.validate_declared_inputs(tmp_path, files)
