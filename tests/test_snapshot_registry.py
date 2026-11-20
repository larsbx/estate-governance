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
        "version": 2,
        "template": "estate-repository-v2",
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


def v3_manifest() -> dict:
    data = manifest(version=3, template="estate-repository-v3")
    data.pop("language")
    data["authority"] = {"acceptance_authority": True}
    data["boundary"] = [{"id": "declaration", "implementation": ["src/checker.goose", "src/bridge.py"],
                         "contract": "docs/contract.md"}]
    data["formalization"] = {
        "scope": "formal/SCOPE.md", "gate": "tools/formal_gate.py",
        "implementation_paths": ["src/checker.goose"],
        "lean": {"sources": ["formal/lean/Checker.lean"],
                 "toolchain": "leanprover/lean4:v4.34.1", "obligations": ["refusal_preserves_state"]},
        "quint": {"sources": ["formal/quint/checker.qnt"],
                  "toolchain": "@informalsystems/quint@0.30.0", "obligations": ["no_stale_evidence"]},
    }
    return data


def test_v3_projection_requires_explicit_registry_contract():
    with pytest.raises(ValueError, match="explicit estate-registry-v2"):
        snap.derive(v3_manifest(), commit=COMMIT, blob=BLOB, ci_gate=True)


def test_v3_projection_carries_declarations_without_inventing_execution():
    data = v3_manifest()
    row = snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)
    assert "canonical_language" not in row
    assert row["manifest_version"] == 3 and row["template"] == "estate-repository-v3"
    assert row["boundaries"] == data["boundary"]
    assert row["boundaries"][0]["implementation"] == ["src/checker.goose", "src/bridge.py"]
    assert row["lean_obligations"] == ["refusal_preserves_state"]
    assert row["quint_sources"] == ["formal/quint/checker.qnt"]
    assert row["formalization_status"] == "not_evaluated"


@pytest.mark.parametrize("lane", ["lean", "quint"])
def test_v3_projection_rejects_a_missing_formalization_lane(lane):
    data = v3_manifest()
    del data["formalization"][lane]
    with pytest.raises(AssertionError, match=lane):
        snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)


@pytest.mark.parametrize("mutation", [
    lambda m: m.update(version=4),
    lambda m: m.update(version=True),
    lambda m: m.update(template="estate-repository-v2"),
])
def test_snapshot_rejects_unknown_or_mismatched_manifest_contract(mutation):
    data = v3_manifest()
    mutation(data)
    with pytest.raises(ValueError, match="manifest"):
        snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)


def test_mixed_registry_round_trip_preserves_versioned_declarations():
    import tomllib
    rows = [snap.derive(manifest(), commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2),
            snap.derive(v3_manifest(), commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)]
    text = snap.render({"version": 2, "governance_source_commit": COMMIT,
                        "required_audit_revisions": {"estate-repository-v2": GOV_REV,
                                                     "estate-repository-v3": "c" * 40}}, rows)
    data = tomllib.loads(text)
    assert data["schema"] == "estate-registry-v2" and data["member"] == rows
    assert rows[0]["canonical_language"] == "Python"
    assert rows[0]["formalization_status"] == "not_evaluated"


def test_legacy_registry_render_is_byte_identical():
    import tomllib
    original = snap.REGISTRY.read_text(encoding="utf-8")
    data = tomllib.loads(original)
    header = {key: data[key] for key in ("governance_source_commit", "required_audit_revision")}
    assert snap.render(header, data["member"]) == original


@pytest.mark.parametrize(("commit", "blob"), [("main", BLOB), (COMMIT, "unknown")])
def test_snapshot_projection_requires_exact_source_identities(commit, blob):
    with pytest.raises(ValueError, match="40-hex identities"):
        snap.derive(manifest(), commit=commit, blob=blob, ci_gate=True)


def test_legacy_adopter_table_is_byte_identical():
    import render_adopters as adopters
    original = adopters.CONTRACT.read_text(encoding="utf-8")
    current_table = original.split(adopters.START, 1)[1].split(adopters.END, 1)[0].strip("\n")
    assert adopters.render() == current_table


def test_v2_registry_table_does_not_invent_formal_compliance():
    import render_adopters as adopters
    row = snap.derive(v3_manifest(), commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)
    data = {"version": 2, "schema": "estate-registry-v2", "member": [row]}
    text = adopters.render(data)
    assert "Canonical language" not in text
    assert "Lean + Quint declared; not evaluated" in text
    row["formalization_status"] = "verified"
    with pytest.raises(AssertionError, match="not_evaluated"):
        adopters.render(data)


def test_v2_registry_cannot_overwrite_the_historical_contract(tmp_path):
    import render_adopters as adopters
    data = snap.render({"version": 2, "governance_source_commit": COMMIT,
                        "required_audit_revisions": {"estate-repository-v3": "c" * 40}},
                       [snap.derive(v3_manifest(), commit=COMMIT, blob=BLOB,
                                    ci_gate=True, registry_version=2)])
    registry = tmp_path / "registry.toml"
    registry.write_text(data)
    with pytest.raises(SystemExit, match="explicit --contract"):
        adopters.update(False, registry=registry)
    with pytest.raises(SystemExit, match="must not overwrite"):
        adopters.update(False, registry=registry, contract=adopters.CONTRACT)


def test_actual_governance_v3_manifest_projects_and_round_trips():
    import tomllib
    source = tomllib.loads((snap.ROOT / "ESTATE.toml").read_text())
    assert source["version"] == 3
    row = snap.derive(source, commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)
    encoded = snap.render({"version": 2, "governance_source_commit": COMMIT,
                           "required_audit_revisions": {"estate-repository-v3": "c" * 40}}, [row])
    parsed = tomllib.loads(encoded)
    assert parsed["member"] == [row]
    assert parsed["member"][0]["boundaries"] == source["boundary"]
    assert all(isinstance(b["implementation"], list) for b in row["boundaries"])
    assert "canonical_language" not in row
    assert audit_estate_registry.validate(parsed)["formalization_evidence"] == "not_evaluated"


@pytest.mark.parametrize("target", ["formalization", "lean", "quint"])
def test_projection_rejects_source_flags_that_disable_required_lanes(target):
    data = v3_manifest()
    table = data["formalization"] if target == "formalization" else data["formalization"][target]
    table["required"] = False
    with pytest.raises(ValueError, match="flags cannot disable"):
        snap.derive(data, commit=COMMIT, blob=BLOB, ci_gate=True, registry_version=2)


def test_v3_snapshot_reads_the_named_commit_not_uncommitted_manifest(tmp_path):
    import subprocess
    data = v3_manifest()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()
    git("init", "--quiet")
    (tmp_path / "ESTATE.toml").write_text("\n".join(
        f"{key} = {snap.toml_value(value)}" for key, value in data.items()) + "\n")
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("run: python kernel/audit_estate_layout.py\n")
    git("add", ".")
    git("-c", "user.name=Snapshot Test", "-c", "user.email=snapshot@example.invalid",
        "commit", "--quiet", "-m", "fixture")
    commit, blob = git("rev-parse", "HEAD"), git("rev-parse", "HEAD:ESTATE.toml")
    (tmp_path / "ESTATE.toml").write_text('version = 99\ntemplate = "uncommitted"\n')
    row = snap.snapshot(tmp_path, commit, registry_version=2)
    assert row["source_commit"] == commit and row["manifest_blob"] == blob
    assert row["manifest_version"] == 3 and row["ci_gate"] is True
    assert row["formalization_status"] == "not_evaluated"


def test_snapshot_upgrade_requires_selection_and_per_contract_revision(tmp_path, monkeypatch):
    import tomllib
    legacy = manifest(dep=[])
    legacy["repo"] = {**legacy["repo"], "id": "estate-governance",
                       "slug": "larsbx/estate-governance", "class": "meta"}
    legacy["exports"] = {"names": []}
    legacy["repo"]["inv"] = []
    legacy["conform"] = []
    modern = v3_manifest()
    modern["dep"] = [{"id": "estate-governance", "rev": "c" * 40, "pin": "sha256:" + "0" * 64}]
    modern["conform"] = []
    manifests = {"estate-governance": legacy, "demo": modern}
    def snapshot_fixture(repo, ref, *, registry_version):
        assert ref == "explicit-ref"
        return snap.derive(manifests[repo.name], commit=COMMIT, blob=BLOB,
                           ci_gate=True, registry_version=registry_version)
    monkeypatch.setattr(snap, "snapshot", snapshot_fixture)
    registry = tmp_path / "registry.toml"
    registry.write_text('version = 1\nschema = "estate-registry-v1"\n'
                        f'governance_source_commit = "{COMMIT}"\nrequired_audit_revision = "{GOV_REV}"\n'
                        '[[member]]\nid = "estate-governance"\n[[member]]\nid = "demo"\n')
    original = registry.read_bytes()
    with pytest.raises(ValueError, match="explicit estate-registry-v2"):
        snap.build(tmp_path, "explicit-ref", registry)
    with pytest.raises(AssertionError, match="no required audit revision"):
        snap.build(tmp_path, "explicit-ref", registry, schema="estate-registry-v2")
    result = snap.build(tmp_path, "explicit-ref", registry, schema="estate-registry-v2",
                        audit_revisions={"estate-repository-v3": "c" * 40})
    data = tomllib.loads(result)
    assert data["required_audit_revisions"] == {"estate-repository-v2": GOV_REV,
                                               "estate-repository-v3": "c" * 40}
    assert data["member"][1]["formalization_status"] == "not_evaluated"
    assert registry.read_bytes() == original


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
