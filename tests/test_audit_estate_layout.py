"""Conformance of the estate audit (estate-repository-v2): one valid baseline, one mutation per rule."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest

import audit_estate_layout as audit

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "kernel" / "audit_estate_layout.py"
KERNELS = "larsbx/finite-math-kernels"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline() -> dict:
    """A research consumer that pins the governance audit it is being checked by."""
    return {
        "version": 2,
        "template": "estate-repository-v2",
        "repo": {"id": "consumer", "slug": "larsbx/consumer", "class": "research", "layer": 3,
                 "band": "EXPLORE", "stage": "candidate", "inv": []},
        "origin": {"decided_by": "proposed", "chats": [], "artifacts": []},
        "layout": {"status": "transitional"},
        "principles": {
            "ordering": ["authority", "domain", "language"],
            "empty_silos": "forbidden",
            "cross_language_disagreement": "fail_closed",
        },
        "plane": [
            {"id": "policy", "target": "policy", "authority": "governance",
             "required": True, "current": ["ESTATE.toml"]},
            {"id": "kernel", "target": "kernel", "authority": "canonical_executable",
             "required": True, "current": ["src"]},
        ],
        "language": [
            {"name": "Python", "authority": "canonical", "roles": ["kernel"],
             "acceptance_authority": True},
        ],
        "dep": [{"id": "estate-governance", "rev": "0" * 40, "pin": "sha256:" + sha256(AUDIT)}],
        "conform": [],
        "exports": {"names": []},
    }


@pytest.fixture
def consumer(tmp_path: Path) -> Path:
    """A minimal consumer tree. It carries no copy of the audit: CI checks governance out."""
    (tmp_path / "src").mkdir()
    (tmp_path / "ESTATE.toml").write_text("", encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    return tmp_path


def test_governance_manifest_is_valid():
    audit.validate(audit.load(ROOT / "ESTATE.toml"), ROOT)


def test_baseline_consumer_is_valid(consumer: Path):
    audit.validate(baseline(), consumer)


DELETE = object()


def mutate(path: str, value) -> Callable[[dict], None]:
    *parents, leaf = path.split(".")

    def apply(data: dict) -> None:
        node = data
        for key in parents:
            node = node[int(key)] if key.isdigit() else node[key]
        key = int(leaf) if leaf.isdigit() else leaf
        if value is DELETE:
            del node[key]
        else:
            node[key] = value

    return apply


REJECTIONS = [
    # identity and SPEC_estate §1/§3 fields
    ("version", 1, "version must be 2"),
    ("template", "estate-repository-v1", "template must be estate-repository-v2"),
    ("repo.id", "Consumer!", "repo.id must be a lowercase repository name"),
    ("repo.slug", "no-owner", "repo.slug must be OWNER/REPOSITORY"),
    ("repo.slug", "larsbx/other", "repo.slug must name repo.id"),
    ("repo.class", "library", "repo.class must be one of"),
    ("repo.layer", 1, "layer 1 differs from the research default 3"),
    ("repo.band", "STRICT", "repo.band must be one of"),
    ("repo.band", "HARDENED", "band HARDENED differs from the research default EXPLORE"),
    ("repo.stage", "ripe", "repo.stage must be one of"),
    ("repo.stage", "seeded", "decided_by = proposed caps the repo at candidate"),
    ("repo.inv", ["FOO"], "INV family prefix"),
    ("origin", DELETE, "origin.decided_by must be stated or proposed"),
    ("origin.decided_by", "assumed", "origin.decided_by must be stated or proposed"),
    ("origin.genesis_suite", "red", "origin.genesis_suite must be green or xfail"),
    ("origin.chats", ["not a link"], "origin.chats must be https links"),
    ("origin.artifacts", [{"path": "a.py", "h": "md5:1"}], "origin.artifacts entries need a path and a sha256"),
    # layout
    ("layout.status", "chaotic", "layout.status must be transitional or canonical"),
    ("principles.ordering", ["language", "domain", "authority"], "ordering"),
    ("principles.cross_language_disagreement", "majority", "fail closed"),
    ("principles.empty_silos", "allowed", "empty silos"),
    ("plane", [], "at least one authority plane"),
    ("plane.1.id", "policy", "duplicate plane id"),
    ("plane.1.target", "policy", "duplicate plane target"),
    ("plane.1.authority", "vibes", "unknown authority"),
    ("plane.1.current", [], "required plane needs a current mapping"),
    ("plane.1.current", ["missing"], "missing current path"),
    ("plane.1.current_globs", ["nothing/*"], "matches nothing"),
    ("plane.1.id", "engine", "kernel plane is required"),
    ("language", [], "exactly one canonical language"),
    ("language.0.roles", ["oracle"], "must own the kernel role"),
    # dependency law (§5) and the governance pin
    ("dep", [], "must depend on estate-governance"),
    ("dep.0.id", "estate", "must depend on estate-governance"),
    ("dep.0.pin", "main", "content hash or signed tag"),
    ("dep.0.pin", "sha256:" + "0" * 64, "does not match the running audit"),
    ("dep.0.rev", "main", "rev must be a 40-hex commit"),
    ("dep.0.rev", DELETE, "rev must be a 40-hex commit"),
    ("conform", [{"id": "oracle"}], "conform oracle: vectors is required"),
    ("exports.names", ["x", "x"], "duplicate export"),
]


@pytest.mark.parametrize(("path", "value", "message"), REJECTIONS, ids=[f"{r[0]}:{r[2]}" for r in REJECTIONS])
def test_each_rule_fails_closed(consumer: Path, path: str, value, message: str):
    data = baseline()
    mutate(path, value)(data)
    with pytest.raises(AssertionError, match=message):
        audit.validate(data, consumer)


def test_a_decision_record_licenses_a_non_default_layer_or_band(consumer: Path):
    data = baseline()
    data["repo"].update(band="HARDENED", override="DR-0001")
    audit.validate(data, consumer)
    data["repo"]["override"] = "because"
    with pytest.raises(AssertionError, match="repo.override must name a decision record"):
        audit.validate(data, consumer)


def test_stated_decisions_may_carry_a_later_stage(consumer: Path):
    data = baseline()
    data["origin"]["decided_by"] = "stated"
    data["repo"]["stage"] = "seeded"
    audit.validate(data, consumer)


def test_supporting_language_cannot_accept(consumer: Path):
    data = baseline()
    data["language"].append({"name": "Julia", "authority": "supporting", "roles": ["oracle"],
                             "acceptance_authority": True})
    with pytest.raises(AssertionError, match="cannot have acceptance authority"):
        audit.validate(data, consumer)


def test_duplicate_language_is_rejected(consumer: Path):
    data = baseline()
    data["language"].append(copy.deepcopy(data["language"][0]))
    with pytest.raises(AssertionError, match="duplicate language"):
        audit.validate(data, consumer)


def test_duplicate_dependency_is_rejected(consumer: Path):
    data = baseline()
    data["dep"].append(copy.deepcopy(data["dep"][0]))
    with pytest.raises(AssertionError, match="duplicate dep"):
        audit.validate(data, consumer)


def test_missing_architecture_entrypoint_is_rejected(consumer: Path):
    (consumer / "ARCHITECTURE.md").unlink()
    with pytest.raises(AssertionError, match="missing architecture entrypoint"):
        audit.validate(baseline(), consumer)


def test_consumers_no_longer_carry_a_copy_of_the_audit(consumer: Path):
    (consumer / "tools").mkdir()
    (consumer / "tools" / "audit_estate_layout.py").write_bytes(AUDIT.read_bytes())
    with pytest.raises(AssertionError, match="vendored copy of the estate audit"):
        audit.validate(baseline(), consumer)


VENDORED_TOML = f'''[[package]]
name = "finite_exact"
repository = "{KERNELS}"
commit = "{"a" * 40}"
root = "vendor/mojo"

[package.files]
"finite_exact/rat_q.mojo" = "{"b" * 64}"
'''


def with_kernels_dep(root: Path) -> dict:
    (root / "vendored.toml").write_text(VENDORED_TOML, encoding="utf-8")
    data = baseline()
    data["dep"].append({"id": "finite-math-kernels", "pin": "sha256:" + audit.vendored_digest(root, KERNELS)})
    return data


def test_a_vendored_dependency_pins_the_digest_of_its_vendored_files(consumer: Path):
    audit.validate(with_kernels_dep(consumer), consumer)


def test_a_vendored_dependency_pin_must_match_vendored_toml(consumer: Path):
    data = with_kernels_dep(consumer)
    (consumer / "vendored.toml").write_text(VENDORED_TOML.replace("b" * 64, "c" * 64), encoding="utf-8")
    with pytest.raises(AssertionError, match="dep finite-math-kernels: pin disagrees with vendored.toml"):
        audit.validate(data, consumer)


def test_vendored_packages_need_a_declared_dependency(consumer: Path):
    (consumer / "vendored.toml").write_text(VENDORED_TOML, encoding="utf-8")
    with pytest.raises(AssertionError, match=f"vendors packages from {KERNELS} without a \\[\\[dep\\]\\]"):
        audit.validate(baseline(), consumer)


def test_pixi_identity_must_agree(consumer: Path):
    (consumer / "pixi.toml").write_text('[workspace]\nname = "other"\n', encoding="utf-8")
    with pytest.raises(AssertionError, match="pixi workspace identity"):
        audit.validate(baseline(), consumer)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('repository = "larsbx/other"\n[estate]\nmanifest = "ESTATE.toml"\n', "repository disagrees"),
        ('repository = "larsbx/consumer"\n[estate]\nmanifest = "estate.toml"\n', "must link to ESTATE.toml"),
    ],
)
def test_polyglot_manifest_must_agree(consumer: Path, body: str, message: str):
    (consumer / "polyglot.manifest.toml").write_text(body, encoding="utf-8")
    with pytest.raises(AssertionError, match=message):
        audit.validate(baseline(), consumer)


def test_meta_class_is_reserved_for_the_governance_repository(consumer: Path):
    data = baseline()
    data["repo"].update(**{"class": "meta"})
    del data["repo"]["layer"]
    with pytest.raises(AssertionError, match="class meta is reserved for larsbx/estate-governance"):
        audit.validate(data, consumer)


def test_governance_source_must_not_depend_on_itself():
    data = audit.load(ROOT / "ESTATE.toml")
    data["dep"] = baseline()["dep"]
    with pytest.raises(AssertionError, match="the estate meta-repo imports nothing"):
        audit.validate(data, ROOT)


def test_main_reports_failure(consumer: Path, capsys):
    assert audit.main(["--root", str(consumer)]) == 1
    assert "estate audit failed" in capsys.readouterr().err


# The canonical layout: every plane at its target, full coverage, empty migration queue.

def canonical(root: Path) -> dict:
    (root / "src").rmdir()
    for target in ("policy", "kernel"):
        (root / target).mkdir(exist_ok=True)
    data = baseline()
    data["layout"]["status"] = "canonical"
    for plane in data["plane"]:
        plane["current"] = [plane["target"]]
    data["plane"].append({"id": "docs", "target": "docs", "authority": "exposition",
                          "current": ["docs", "ARCHITECTURE.md"]})
    (root / "docs").mkdir()
    return data


def test_canonical_layout_requires_every_plane_at_its_target(consumer: Path):
    data = baseline()
    data["layout"]["status"] = "canonical"
    with pytest.raises(AssertionError, match="canonical layout: plane policy must map its target"):
        audit.validate(data, consumer)


def test_canonical_layout_passes_when_every_directory_is_claimed(consumer: Path):
    audit.validate(canonical(consumer), consumer)


def test_canonical_layout_rejects_glob_mappings(consumer: Path):
    data = canonical(consumer)
    data["plane"][1]["current_globs"] = ["kern*"]
    with pytest.raises(AssertionError, match="canonical layout: plane kernel must map its target"):
        audit.validate(data, consumer)


def test_canonical_layout_requires_an_empty_migration_queue(consumer: Path):
    data = canonical(consumer)
    data["migration"] = {"next": ["one more move"]}
    with pytest.raises(AssertionError, match="canonical layout must have no pending migration"):
        audit.validate(data, consumer)


def test_canonical_layout_rejects_an_unclaimed_top_level_directory(consumer: Path):
    data = canonical(consumer)
    (consumer / "bin").mkdir()
    with pytest.raises(AssertionError, match="canonical layout: top-level directory 'bin' belongs to no plane"):
        audit.validate(data, consumer)


def test_canonical_coverage_ignores_hidden_and_build_directories(consumer: Path):
    data = canonical(consumer)
    for name in (".github", ".estate", "__pycache__", "pkg.egg-info", "build", "dist", "coverage"):
        (consumer / name).mkdir()
    audit.validate(data, consumer)


@pytest.mark.parametrize("name", ["builds", "distribution", "coverages", "src"])
def test_canonical_coverage_exempts_build_outputs_by_exact_name_only(consumer: Path, name: str):
    data = canonical(consumer)
    (consumer / name).mkdir(exist_ok=True)
    with pytest.raises(AssertionError, match=f"top-level directory '{name}' belongs to no plane"):
        audit.validate(data, consumer)
