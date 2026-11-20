from __future__ import annotations

import copy

import pytest

import audit_estate_registry


def load_current():
    return audit_estate_registry.load()


def member(data, member_id):
    return next(row for row in data["member"] if row["id"] == member_id)


def test_current_registry_passes():
    data = load_current()
    summary = audit_estate_registry.validate(data)
    assert summary["members"] >= 10
    # The snapshot commit moves with every regeneration; it must name the governance row.
    assert summary["governance_source_commit"] == data["governance_source_commit"]
    assert summary["required_audit_revision"] == "5ea47dec8086eab6a1dad6fd239688d20ea89891"


def test_dependency_cycle_fails():
    data = copy.deepcopy(load_current())
    member(data, "novelty-lab")["deps"] = ["langlands-lab"]
    member(data, "langlands-lab")["deps"] = ["novelty-lab"]
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
    with pytest.raises(AssertionError, match="governance audit revision is stale"):
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


def mixed_registry():
    data = copy.deepcopy(load_current())
    legacy_revision = data.pop("required_audit_revision")
    data.update(version=2, schema="estate-registry-v2", required_audit_revisions={
        "estate-repository-v2": legacy_revision, "estate-repository-v3": "c" * 40,
    })
    for row in data["member"]:
        row.update(manifest_version=2, template="estate-repository-v2",
                   formalization_status="not_evaluated")
    row = member(data, "langlands-lab")
    row.pop("canonical_language")
    row.update(manifest_version=3, template="estate-repository-v3", governance_rev="c" * 40,
               boundaries=[{"id": "claims", "implementation": ["kernel/checker.py", "src/bridge.goose"],
                            "contract": "docs/contract.md"}],
               formalization_scope="formal/SCOPE.md", formalization_gate="tools/formal_gate.py",
               implementation_paths=["kernel/checker.py"],
               lean_sources=["formal/lean/Claims.lean"], lean_toolchain="leanprover/lean4:v4.34.1",
               lean_obligations=["failure_preserves_state"],
               quint_sources=["formal/quint/claims.qnt"], quint_toolchain="@informalsystems/quint@0.30.0",
               quint_obligations=["no_stale_evidence"])
    return data


def test_mixed_contract_registry_preserves_legacy_pins_and_marks_evidence_unassessed():
    data = mixed_registry()
    summary = audit_estate_registry.validate(data)
    assert summary["manifest_versions"] == {"2": 20, "3": 1}
    assert summary["formalization_evidence"] == "not_evaluated"
    assert summary["required_audit_revisions"]["estate-repository-v2"] == \
        load_current()["required_audit_revision"]


@pytest.mark.parametrize(("mutation", "message"), [
    (lambda d: d.update(version=3), "registry version"),
    (lambda d: d.update(version=True), "registry version"),
    (lambda d: d.update(schema="estate-registry-v1"), "registry schema"),
    (lambda d: d.update(required_audit_revision="c" * 40), "per-template audit revisions"),
    (lambda d: d["required_audit_revisions"].update(other="c" * 40), "unknown auditor manifest"),
    (lambda d: d["required_audit_revisions"].pop("estate-repository-v3"), "no required audit revision"),
    (lambda d: member(d, "langlands-lab").update(governance_rev="d" * 40), "audit revision is stale"),
    (lambda d: member(d, "langlands-lab").update(formalization_status="passed"), "not_evaluated"),
    (lambda d: member(d, "langlands-lab").update(manifest_version=4), "unsupported manifest_version"),
    (lambda d: member(d, "langlands-lab").update(template="estate-repository-v2"), "template disagree"),
    (lambda d: member(d, "langlands-lab").update(canonical_language="Python"), "canonical_language"),
    (lambda d: member(d, "langlands-lab").update(boundaries=[]), "named boundary"),
    (lambda d: member(d, "langlands-lab").update(acceptance_authority=False), "named boundary"),
    (lambda d: member(d, "langlands-lab")["boundaries"][0].update(id="Unstable ID"), "lowercase and stable"),
    (lambda d: member(d, "langlands-lab")["boundaries"][0].update(implementation="kernel/checker.py"), "string list"),
    (lambda d: member(d, "langlands-lab")["boundaries"][0].update(implementation=["x.py", "x.py"]), "duplicates"),
    (lambda d: member(d, "langlands-lab").update(lean_sources=[]), "lean_sources"),
    (lambda d: member(d, "langlands-lab").pop("quint_toolchain"), "quint_toolchain"),
    (lambda d: member(d, "langlands-lab").update(quint_toolchain="@informalsystems/quint@latest"), "exact version"),
    (lambda d: member(d, "langlands-lab").update(quint_obligations=[]), "quint_obligations"),
    (lambda d: member(d, "langlands-lab").update(formalization_scope="../outside.md"), "relative declared"),
    (lambda d: member(d, "langlands-lab").update(ci_gate=False), "estate CI gate"),
    (lambda d: d.update(governance_source_commit="d" * 40), "must equal estate-governance"),
])
def test_mixed_registry_refuses_invalid_or_overstated_declarations(mutation, message):
    data = mixed_registry()
    mutation(data)
    with pytest.raises(AssertionError, match=message):
        audit_estate_registry.validate(data)


def test_legacy_registry_cannot_silently_reinterpret_a_v3_row():
    data = load_current()
    member(data, "langlands-lab").update(manifest_version=3, template="estate-repository-v3")
    with pytest.raises(AssertionError, match="require estate-registry-v2"):
        audit_estate_registry.validate(data)


def test_historical_language_is_required_only_for_v2_rows():
    data = mixed_registry()
    assert "canonical_language" not in member(data, "langlands-lab")
    audit_estate_registry.validate(data)
    member(data, "novelty-lab").pop("canonical_language")
    with pytest.raises(AssertionError, match="historical v2"):
        audit_estate_registry.validate(data)


def test_exact_formal_toolchain_versions_are_consumer_specific_declarations():
    data = mixed_registry()
    member(data, "langlands-lab").update(lean_toolchain="leanprover/lean4:v4.31.0",
                                        quint_toolchain="@informalsystems/quint@0.25.0")
    summary = audit_estate_registry.validate(data)
    assert summary["formalization_evidence"] == "not_evaluated"


def test_nonaccepting_v3_member_has_no_accepting_boundaries():
    data = mixed_registry()
    member(data, "langlands-lab").update(acceptance_authority=False, boundaries=[])
    audit_estate_registry.validate(data)
