from __future__ import annotations

import copy
from pathlib import Path

import pytest

import audit_estate_registry
import snapshot_registry as snap

COMMIT = "a" * 40
BLOB = "b" * 40
GOV_REV = "5ea47dec8086eab6a1dad6fd239688d20ea89891"


def manifest(**overrides) -> dict:
    data = {
        "repo": {"id": "demo", "slug": "larsbx/demo", "class": "research", "layer": 3,
                 "band": "EXPLORE", "stage": "candidate", "inv": ["INV-DM"]},
        "origin": {"decided_by": "stated", "decision": "DR-0001"},
        "dep": [{"id": "estate-governance", "rev": GOV_REV, "pin": "sha256:" + "0" * 64},
                {"id": "finite-math-kernels", "rev": COMMIT, "pin": "sha256:" + "1" * 64}],
        "conform": [{"id": "finite-math-kernels", "vectors": "v1"},
                    {"id": "finite-math-kernels", "vectors": "v2"}],
        "exports": {"names": ["demo_export"]},
        "language": [{"name": "Python", "authority": "canonical", "acceptance_authority": True},
                     {"name": "Lean", "authority": "supporting"}],
    }
    data.update(overrides)
    return data


def test_derive_maps_every_registry_field():
    row = snap.derive(manifest(), commit=COMMIT, blob=BLOB, ci_gate=True)
    assert row == {
        "id": "demo", "slug": "larsbx/demo", "source_commit": COMMIT, "manifest_blob": BLOB,
        "class": "research", "layer": 3, "band": "EXPLORE", "stage": "candidate",
        "canonical_language": "Python", "acceptance_authority": True,
        "decided_by": "stated", "decision": "DR-0001",
        "governance_rev": GOV_REV, "inv": ["INV-DM"], "exports": ["demo_export"],
        "deps": ["finite-math-kernels"], "conforms": ["finite-math-kernels"], "ci_gate": True,
    }


def test_derive_meta_member_sits_outside_layering():
    data = manifest(dep=[])
    data["repo"] = {**data["repo"], "id": "estate-governance", "slug": "larsbx/estate-governance",
                    "class": "meta", "band": "STANDARD"}
    del data["repo"]["layer"]
    row = snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True)
    assert row["layer"] == -1 and "governance_rev" not in row and row["deps"] == []


def test_derive_multi_program_carries_claim_namespaces():
    data = manifest(workspace={"mode": "multi_program"},
                    program=[{"id": "a", "claim_namespace": "AA"}, {"id": "b", "claim_namespace": "BB"}])
    row = snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True)
    assert row["workspace"] == "multi_program" and row["claim_namespaces"] == ["AA", "BB"]


def test_derive_omits_decision_when_proposed():
    data = manifest(origin={"decided_by": "proposed"})
    row = snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True)
    assert row["decided_by"] == "proposed" and "decision" not in row


def test_render_round_trips_through_toml():
    import tomllib
    rows = [snap.derive(manifest(), commit=COMMIT, blob=BLOB, ci_gate=True)]
    text = snap.render({"governance_source_commit": COMMIT, "required_audit_revision": GOV_REV}, rows)
    data = tomllib.loads(text)
    assert data["schema"] == "estate-registry-v1" and data["member"] == rows


def test_ci_gate_detects_the_pinned_audit_step():
    assert snap.has_ci_gate(["run: python3 /tmp/estate-audit.py --root .\n"
                             'url "https://raw.githubusercontent.com/larsbx/estate-governance/$rev/kernel/audit_estate_layout.py"'])
    assert snap.has_ci_gate(["run: python kernel/audit_estate_layout.py"])
    assert not snap.has_ci_gate(["run: pytest"])


# --- decision records in the estate-wide audit ---------------------------------

def current() -> dict:
    return copy.deepcopy(audit_estate_registry.load())


def first(data: dict) -> dict:
    return next(m for m in data["member"] if m["id"] != "estate-governance")


def test_stated_member_must_name_a_decision_record():
    data = current()
    first(data).pop("decision", None)
    first(data)["decided_by"] = "stated"
    with pytest.raises(AssertionError, match="must name a decision record"):
        audit_estate_registry.validate(data)


def test_stated_member_decision_record_must_exist():
    data = current()
    first(data).update(decided_by="stated", decision="DR-9999")
    with pytest.raises(AssertionError, match="no accepted decision record DR-9999"):
        audit_estate_registry.validate(data)


def test_proposed_member_is_capped_at_candidate():
    data = current()
    first(data).update(decided_by="proposed", stage="seeded")
    first(data).pop("decision", None)
    with pytest.raises(AssertionError, match="caps the stage at candidate"):
        audit_estate_registry.validate(data)


def test_decision_record_must_be_accepted(tmp_path: Path):
    record = tmp_path / "DR-0007-x.md"
    record.write_text("# DR-0007 — x\n\n- **Status:** proposed\n")
    assert not audit_estate_registry.accepted_decisions(tmp_path)
    record.write_text("# DR-0007 — x\n\n- **Status:** accepted\n")
    assert audit_estate_registry.accepted_decisions(tmp_path) == {"DR-0007"}


# --- archived members release their names -------------------------------------

def test_archived_member_releases_its_claim_namespaces():
    data = current()
    pilot = member_by_id(data, "finite-dynamics")
    pilot.update(workspace="multi_program", claim_namespaces=["FM", "FJ"], stage="archived")
    audit_estate_registry.validate(data, decisions=accepted_ids(data))


def test_active_members_still_collide_on_claim_namespaces():
    data = current()
    pilot = member_by_id(data, "finite-dynamics")
    pilot.update(workspace="multi_program", claim_namespaces=["FM", "FJ"], stage="candidate")
    member_by_id(data, "novelty-lab").update(workspace="multi_program", claim_namespaces=["FM", "NOV"])
    with pytest.raises(AssertionError, match="duplicate claim namespace"):
        audit_estate_registry.validate(data, decisions=accepted_ids(data))


def test_archived_member_releases_exports_and_inv():
    data = current()
    pilot = member_by_id(data, "finite-dynamics")
    pilot.update(stage="archived", exports=["finite_exact"], inv=["INV-ABC"])
    audit_estate_registry.validate(data, decisions=accepted_ids(data))


def member_by_id(data: dict, member_id: str) -> dict:
    return next(m for m in data["member"] if m["id"] == member_id)


def accepted_ids(data: dict) -> set[str]:
    return {m["decision"] for m in data["member"] if m.get("decision")}
