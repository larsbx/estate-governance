from __future__ import annotations

import copy

import pytest

import audit_estate_registry


def load_current():
    return audit_estate_registry.load()


def member(data, member_id):
    return next(row for row in data["member"] if row["id"] == member_id)


def test_current_registry_passes():
    summary = audit_estate_registry.validate(load_current())
    assert summary["members"] >= 10
    assert summary["governance_revision"] == "5ea47dec8086eab6a1dad6fd239688d20ea89891"


def test_dependency_cycle_fails():
    data = copy.deepcopy(load_current())
    member(data, "finite-math-kernels")["deps"] = ["finite-mandelbrot-research"]
    with pytest.raises(AssertionError, match="code dependency cycle"):
        audit_estate_registry.validate(data)


def test_upward_dependency_fails():
    data = copy.deepcopy(load_current())
    member(data, "finite-math-kernels")["deps"] = ["finite-mandelbrot-research"]
    # Remove the reverse edge so the failure is specifically layering, not cycle.
    member(data, "finite-mandelbrot-research")["deps"] = []
    with pytest.raises(AssertionError, match="depends upward"):
        audit_estate_registry.validate(data)


def test_duplicate_export_fails():
    data = copy.deepcopy(load_current())
    member(data, "finite-mandelbrot-research")["exports"] = ["finite_exact"]
    with pytest.raises(AssertionError, match="duplicate export"):
        audit_estate_registry.validate(data)


def test_duplicate_inv_prefix_fails():
    data = copy.deepcopy(load_current())
    member(data, "arithmetic-bicycle-conjecture-research")["inv"] = ["INV-VDC"]
    with pytest.raises(AssertionError, match="duplicate INV prefix"):
        audit_estate_registry.validate(data)


def test_stale_governance_revision_fails():
    data = copy.deepcopy(load_current())
    member(data, "langlands-lab")["governance_rev"] = "0" * 40
    with pytest.raises(AssertionError, match="governance revision is stale"):
        audit_estate_registry.validate(data)


def test_missing_estate_ci_gate_fails():
    data = copy.deepcopy(load_current())
    member(data, "vizing-domination-conjecture-research")["ci_gate"] = False
    with pytest.raises(AssertionError, match="estate CI gate"):
        audit_estate_registry.validate(data)


def test_unknown_dependency_fails():
    data = copy.deepcopy(load_current())
    member(data, "novelty-lab")["deps"] = ["not-registered"]
    with pytest.raises(AssertionError, match="unregistered member"):
        audit_estate_registry.validate(data)


def test_reciprocal_conformance_is_allowed():
    data = copy.deepcopy(load_current())
    assert member(data, "finite-math-kernels")["conforms"] == ["julia-oracle-lab"]
    assert member(data, "julia-oracle-lab")["conforms"] == ["finite-math-kernels"]
    audit_estate_registry.validate(data)


def test_claim_namespaces_are_estate_unique():
    data = copy.deepcopy(load_current())
    member(data, "novelty-lab")["workspace"] = "multi_program"
    member(data, "novelty-lab")["claim_namespaces"] = ["FM", "NOV"]
    with pytest.raises(AssertionError, match="duplicate claim namespace"):
        audit_estate_registry.validate(data)
