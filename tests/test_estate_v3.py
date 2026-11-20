"""Contract migration tests: language freedom, explicit authority, real formal inputs.

These are manifest-validation fixtures, not Lean/Quint execution evidence.
The independent formal workflow executes the repository's actual formal sources.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

import audit_estate_layout as audit


@pytest.fixture
def v3(tmp_path: Path) -> tuple[dict, Path]:
    files = {
        "ESTATE.toml": "# test fixture, represented by the dict below\n",
        "ARCHITECTURE.md": "# Test authority and formal scope\n",
        "src/checker.goose": "fn main() { }\n",
        "src/adapter.py": "def observe(): return False\n",
        "docs/formalization.md": "# Test fixture only; no executed proof claim\n",
        "tools/formal.py": "# Test gate declaration, not execution evidence\n",
        "proof/Scope.lean": "theorem scope_identity (p : Prop) : p → p := fun h => h\n",
        "model/scope.qnt": "module scope { val invariant = true }\n",
    }
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    data = {
        "version": 3,
        "template": "estate-repository-v3",
        "repo": {"id": "consumer", "slug": "larsbx/consumer", "class": "research",
                 "layer": 3, "band": "EXPLORE", "stage": "candidate", "inv": []},
        "origin": {"decided_by": "proposed", "chats": [], "artifacts": []},
        "principles": {"ordering": ["authority", "domain"], "disagreement": "fail_closed",
                       "empty_silos": "forbidden", "generated_surfaces": "derived_only",
                       "vendor_code": "non_local", "experimental_code": "non_authoritative"},
        "authority": {"acceptance_authority": False},
        "formalization": {
            "scope": "docs/formalization.md", "gate": "tools/formal.py",
            "implementation_paths": ["src/checker.goose", "src/adapter.py"],
            "lean": {"toolchain": "leanprover/lean4:v4.34.1", "sources": ["proof/Scope.lean"],
                     "obligations": ["scope_identity"]},
            "quint": {"toolchain": "@informalsystems/quint@0.33.1", "sources": ["model/scope.qnt"],
                      "obligations": ["invariant"]},
        },
        "dep": [{"id": "estate-governance", "rev": "a" * 40,
                 "pin": "sha256:" + audit.sha256(Path(audit.__file__))}],
        "exports": {"names": []},
    }
    return data, tmp_path


def test_v3_requires_no_language_kernel_or_plane_skeleton(v3):
    data, root = v3
    assert not {"language", "plane", "layout"}.intersection(data)
    assert not (root / "kernel").exists()
    audit.validate(data, root)


@pytest.mark.parametrize("value", [False, 0, "", {}, "planes", [False], ["policy"]])
def test_declared_plane_inventory_cannot_bypass_validation_with_a_wrong_type(v3, value):
    data, root = v3
    data["plane"] = value
    with pytest.raises(AssertionError, match="array of tables"):
        audit.validate(data, root)


@pytest.mark.parametrize("value", [False, 0, "", [], "canonical"])
def test_declared_layout_must_be_a_table(v3, value):
    data, root = v3
    data["layout"] = value
    with pytest.raises(AssertionError, match="layout must be a table"):
        audit.validate(data, root)


def test_language_inventory_has_no_authority_effect(v3):
    data, root = v3
    # Old descriptive inventory cannot override the independent v3 boundary.
    data["language"] = [{"name": "Goose", "authority": "canonical", "acceptance_authority": True},
                        {"name": "Python", "authority": "canonical", "acceptance_authority": True}]
    audit.validate(data, root)
    assert data["authority"]["acceptance_authority"] is False


def test_a_boundary_can_be_implemented_in_multiple_languages(v3):
    data, root = v3
    data["authority"]["acceptance_authority"] = True
    data["boundary"] = [{"id": "check-input", "implementation": ["src/checker.goose", "src/adapter.py"],
                         "contract": "ARCHITECTURE.md"}]
    audit.validate(data, root)


@pytest.mark.parametrize("value", [None, "true", 1, 0, [], {}])
def test_boundary_authority_is_an_explicit_boolean(v3, value):
    data, root = v3
    data["authority"]["acceptance_authority"] = value
    with pytest.raises(AssertionError, match="explicit boolean"):
        audit.validate(data, root)


@pytest.mark.parametrize("accepts, boundaries", [
    (True, []),
    (False, [{"id": "check", "implementation": ["src/checker.goose"], "contract": "ARCHITECTURE.md"}]),
])
def test_declared_authority_matches_named_boundaries(v3, accepts, boundaries):
    data, root = v3
    data["authority"]["acceptance_authority"] = accepts
    data["boundary"] = boundaries
    with pytest.raises(AssertionError, match="presence of named accepting boundaries"):
        audit.validate(data, root)


def test_duplicate_boundary_is_refused(v3):
    data, root = v3
    data["authority"]["acceptance_authority"] = True
    boundary = {"id": "check", "implementation": ["src/checker.goose"], "contract": "ARCHITECTURE.md"}
    data["boundary"] = [boundary, copy.deepcopy(boundary)]
    with pytest.raises(AssertionError, match="duplicate boundary"):
        audit.validate(data, root)


@pytest.mark.parametrize("lane", ["lean", "quint"])
def test_both_formal_lanes_are_required(v3, lane):
    data, root = v3
    del data["formalization"][lane]
    with pytest.raises(AssertionError, match=f"formalization.{lane} is required"):
        audit.validate(data, root)


@pytest.mark.parametrize("lane, toolchain", [
    ("lean", "leanprover/lean4:stable"), ("lean", "leanprover/lean4:nightly"),
    ("quint", "@informalsystems/quint@latest"), ("quint", "@informalsystems/quint@^0.33.1"),
])
def test_formal_toolchains_cannot_float(v3, lane, toolchain):
    data, root = v3
    data["formalization"][lane]["toolchain"] = toolchain
    with pytest.raises(AssertionError, match="exact toolchain version"):
        audit.validate(data, root)


@pytest.mark.parametrize("lane, field, value", [
    ("lean", "sources", []), ("quint", "sources", []),
    ("lean", "obligations", []), ("quint", "obligations", []),
    ("lean", "obligations", ["todo someday"]),
    ("quint", "obligations", ["invariant", "invariant"]),
    ("lean", "sources", ["docs/formalization.md"]),
    ("quint", "sources", ["missing.qnt"]),
])
def test_plans_and_missing_formal_artifacts_do_not_satisfy_declarations(v3, lane, field, value):
    data, root = v3
    data["formalization"][lane][field] = value
    with pytest.raises(AssertionError):
        audit.validate(data, root)


@pytest.mark.parametrize("lane", [None, "lean", "quint"])
@pytest.mark.parametrize("field, value", [("enabled", False), ("required", False), ("status", "passed")])
def test_flags_cannot_disable_or_certify_formal_execution(v3, lane, field, value):
    data, root = v3
    target = data["formalization"] if lane is None else data["formalization"][lane]
    target[field] = value
    with pytest.raises(AssertionError, match="flags cannot disable or certify"):
        audit.validate(data, root)


@pytest.mark.parametrize("field", ["scope", "gate", "implementation_paths"])
def test_scope_gate_and_implementation_mapping_are_required(v3, field):
    data, root = v3
    del data["formalization"][field]
    with pytest.raises(AssertionError, match=f"formalization.{field}"):
        audit.validate(data, root)


def test_empty_formal_source_is_refused(v3):
    data, root = v3
    (root / "proof/Scope.lean").write_text("")
    with pytest.raises(AssertionError, match="empty file is not an artifact"):
        audit.validate(data, root)


@pytest.mark.parametrize("path", ["../outside.lean", "/tmp/outside.lean", "proof/../proof/Scope.lean"])
def test_formal_source_path_escape_is_refused(v3, path):
    data, root = v3
    data["formalization"]["lean"]["sources"] = [path]
    with pytest.raises(AssertionError, match="repository-relative"):
        audit.validate(data, root)


def test_formal_source_symlink_is_refused(v3, tmp_path):
    data, root = v3
    (root / "proof/link.lean").symlink_to(root / "proof/Scope.lean")
    data["formalization"]["lean"]["sources"] = ["proof/link.lean"]
    with pytest.raises(AssertionError, match="missing owned file"):
        audit.validate(data, root)


def declare_programs(data: dict, root: Path) -> None:
    data["workspace"] = {"mode": "multi_program"}
    data["program"] = []
    for name, namespace in (("one", "ONE"), ("two", "TWO")):
        directory = root / "programs" / name
        directory.mkdir(parents=True)
        (directory / "PROGRAM.toml").write_text(f'version = 1\n[program]\nid = "{name}"\n')
        data["program"].append({"id": name, "root": f"programs/{name}", "claim_namespace": namespace})


def test_multi_program_has_no_canonical_language_or_collection_plane_requirement(v3):
    data, root = v3
    declare_programs(data, root)
    audit.validate(data, root)


@pytest.mark.parametrize("kind", ["program", "child-manifest", "shared"])
def test_workspace_paths_cannot_escape_via_symlinks(v3, tmp_path_factory, kind):
    data, root = v3
    declare_programs(data, root)
    outside = tmp_path_factory.mktemp("external-program")
    (outside / "PROGRAM.toml").write_text('version = 1\n[program]\nid = "one"\n')
    if kind == "program":
        directory = root / "programs/one"
        (directory / "PROGRAM.toml").unlink()
        directory.rmdir()
        directory.symlink_to(outside)
        message = "root escapes repository"
    elif kind == "child-manifest":
        manifest = root / "programs/one/PROGRAM.toml"
        manifest.unlink()
        manifest.symlink_to(outside / "PROGRAM.toml")
        message = "child manifest escapes"
    else:
        (root / "shared").mkdir()
        (root / "shared/core").symlink_to(outside)
        data["shared_component"] = [{"id": "core", "root": "shared/core", "consumers": ["one", "two"]}]
        message = "root escapes repository"
    with pytest.raises(AssertionError, match=message):
        audit.validate(data, root)


def test_julia_oracle_needs_no_special_language_inventory(v3):
    data, root = v3
    (root / "oracles/julia").mkdir(parents=True)
    (root / "polyglot.manifest.toml").write_text(
        'repository = "larsbx/consumer"\n[estate]\nmanifest = "ESTATE.toml"\n')
    audit.validate(data, root)


def test_v3_audit_never_claims_execution(v3, monkeypatch, capsys):
    data, root = v3
    monkeypatch.setattr(audit, "load", lambda _: data)
    assert audit.main(["--root", str(root)]) == 0
    output = capsys.readouterr().out
    assert "manifest audit passed" in output
    assert "execution remains a separate required gate" in output


def test_version_and_template_cannot_be_mixed(v3):
    data, root = v3
    data["template"] = "estate-repository-v2"
    with pytest.raises(AssertionError, match="template must be estate-repository-v3"):
        audit.validate(data, root)
