"""Fail-closed mutation and selection tests for estate-ci-impact-v1."""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

import ci_impact_policy as impact

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy() -> dict:
    return copy.deepcopy(impact.load(ROOT / "policy/ci-impact.toml"))


def checked(policy: dict) -> dict:
    return impact.validate(policy, ROOT)


def test_repository_policy_is_valid(policy):
    model = checked(policy)
    assert len(model["components"]) >= 5
    assert "governance-policy" in model["suites"]


@pytest.mark.parametrize(("mutation", "error"), [
    (lambda p: p.update(version=2), "unsupported policy version"),
    (lambda p: p.update(schema="other"), "unknown impact schema"),
    (lambda p: p.update(repository="larsbx/other"), "differs from ESTATE.toml"),
    (lambda p: p.update(foo="x"), "unknown keys"),
    (lambda p: p["selection"].update(unmapped="skip"), "must force full"),
    (lambda p: p["selection"].update(extra="x"), "unknown keys"),
    (lambda p: p["selection"].update(full_on=["../secrets/**"]), "unsafe or unsupported"),
    (lambda p: p["selection"].update(full_on=["docs/*"]), "unsafe or unsupported"),
    (lambda p: p["selection"].update(ignore=["policy/**"]), "overlap"),
    (lambda p: p["component"][0].update(extra=True), "unknown keys"),
    (lambda p: p["component"].append(copy.deepcopy(p["component"][0])), "duplicate component"),
    (lambda p: p["component"][1].update(paths=p["component"][0]["paths"]), "ambiguous path ownership"),
    (lambda p: p["component"][1].update(depends_on=["missing"]), "unknown dependency"),
    (lambda p: p["component"][0].update(depends_on=["layout"]), "self-dependency"),
    (lambda p: p["component"][0].update(depends_on=["snapshot"]), "cycle"),
    (lambda p: p["suite"][0].update(mode="accept"), "unknown mode"),
    (lambda p: p["suite"][0].update(command=["sh", "-c", "echo yes"]), "unknown keys"),
    (lambda p: p["suite"][0].update(entrypoints=["missing_test.py"]), "missing or escaping entrypoint"),
    (lambda p: p["suite"][0].update(entrypoints=["../../etc/passwd"]), "unsafe or unsupported"),
    (lambda p: p["suite"][1].update(components=["unknown"]), "unknown component"),
    (lambda p: p["suite"][0].update(mode="affected"), "at least one always-run"),
    (lambda p: p["suite"].append(copy.deepcopy(p["suite"][0])), "duplicate suite"),
])
def test_invalid_mutations_are_rejected(policy, mutation, error):
    mutation(policy)
    with pytest.raises(impact.PolicyError, match=error):
        checked(policy)


def test_docs_only_selects_preflight_and_explains_skips(policy):
    model = checked(policy)
    result = impact.plan(policy, model, ["README.md", "docs/audits/example.md"])
    assert result["decision"] == "preflight-only"
    assert result["selected_suites"] == ["governance-policy"]
    assert len(result["skipped_suites"]) == len(model["suites"]) - 1
    assert result["source_coverage"] == "local-only"
    assert result["verdict"] == "selection-plan-only"


def test_transitive_reverse_dependencies(policy):
    result = impact.plan(policy, checked(policy), ["kernel/audit_estate_layout.py"])
    assert result["decision"] == "targeted"
    assert result["dependency_closure"] == ["layout", "pin", "registry", "render", "snapshot"]
    assert result["selected_suites"] == [
        "governance-policy", "layout", "pin", "registry", "render", "snapshot"
    ]


def test_single_change_selects_affected_plus_always(policy):
    result = impact.plan(policy, checked(policy), ["tools/pin_estate.py"])
    assert result["selected_suites"] == ["governance-policy", "pin"]


@pytest.mark.parametrize("paths", [
    ["some-new-tool.py"],
    ["README.md", "some-new-tool.py"],
    ["kernel/audit_estate_registry.py", "unknown.c"],
    ["policy/ci-impact.toml"],
    [".github/workflows/ci.yml"],
    ["tests/test_ci_impact_policy.py"],
])
def test_critical_or_unknown_changes_force_full(policy, paths):
    model = checked(policy)
    result = impact.plan(policy, model, paths)
    assert result["decision"] == "full"
    assert result["selected_suites"] == sorted(model["suites"])
    assert result["reasons"]
    assert not result["skipped_suites"]


def test_explicit_full_and_empty_delta(policy):
    model = checked(policy)
    full = impact.plan(policy, model, [], force_full=True)
    assert full["selected_suites"] == sorted(model["suites"])
    empty = impact.plan(policy, model, [])
    assert empty["selected_suites"] == ["governance-policy"]


@pytest.mark.parametrize("bad", [
    "/etc/passwd", "../test.py", "./test.py", "x//file.py",
    "a\\b", "a\nB", "",
])
def test_malicious_or_ambiguous_changed_paths_block(policy, bad):
    with pytest.raises(impact.PolicyError, match="invalid changed path"):
        impact.plan(policy, checked(policy), [bad])


def test_git_comparison_rejects_invalid_and_stale_source_identifiers():
    with pytest.raises(impact.PolicyError, match="invalid comparison base"):
        impact.git_diff(ROOT, "main", "a" * 40)
    with pytest.raises(impact.PolicyError, match="tested SHA does not match"):
        impact.git_diff(ROOT, "a" * 40, "b" * 40)


def test_main_check_cli_passes(capsys):
    status = impact.main(["--check", "--root", str(ROOT)])
    assert status == 0
    assert "validated" in capsys.readouterr().out


def test_main_rejects_unsafe_cli_configuration(capsys, tmp_path):
    status = impact.main(["--check", "--root", str(ROOT), "--path", "README.md"])
    assert status == 2
    assert "BLOCKED" in capsys.readouterr().err


def test_main_plan_is_non_authoritative(capsys, tmp_path):
    output = tmp_path / "plan.json"
    status = impact.main(["--root", str(ROOT), "--path", "README.md",
                          "--output", str(output)])
    assert status == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["tested_revision"] is None
    assert receipt["policy_digest"].startswith("sha256:")
    assert receipt["selected_suites"] == ["governance-policy"]
    assert receipt["verdict"] == "selection-plan-only"
