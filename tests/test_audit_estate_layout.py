"""Conformance of the estate-layout audit: one valid baseline, one mutation per rule."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Callable
from pathlib import Path

import pytest

import audit_estate_layout as audit

ROOT = Path(__file__).resolve().parents[1]

CONSUMER = "larsbx/consumer"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline() -> dict:
    return {
        "version": 1,
        "template": "estate-repository-v1",
        "repository": {"id": CONSUMER, "layout_status": "transitional"},
        "principles": {
            "ordering": ["authority", "domain", "language"],
            "empty_silos": "forbidden",
            "cross_language_disagreement": "fail_closed",
        },
        "plane": [
            {"id": "policy", "target": "policy", "authority": "governance",
             "required": True, "current": ["estate.toml"]},
            {"id": "kernel", "target": "kernel", "authority": "canonical_executable",
             "required": True, "current": ["src"]},
        ],
        "language": [
            {"name": "Python", "authority": "canonical", "roles": ["kernel"],
             "acceptance_authority": True},
        ],
        "governance": {"repository": audit.GOVERNANCE_REPOSITORY, "revision": "0" * 40},
    }


@pytest.fixture
def consumer(tmp_path: Path) -> Path:
    """A minimal consumer tree carrying byte-identical vendored governance files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "estate.toml").write_text("", encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    for local, source in audit.VENDORED.items():
        target = tmp_path / local
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / source).read_bytes())
    return tmp_path


def pinned(root: Path) -> dict:
    data = baseline()
    data["governance"]["sha256"] = {rel: sha256(root / rel) for rel in audit.VENDORED}
    return data


def test_governance_manifest_is_valid():
    audit.validate(audit.load(ROOT / "estate.toml"), ROOT)


def test_baseline_consumer_is_valid(consumer: Path):
    audit.validate(pinned(consumer), consumer)


def mutate(path: str, value) -> Callable[[dict], None]:
    *parents, leaf = path.split(".")

    def apply(data: dict) -> None:
        node = data
        for key in parents:
            node = node[int(key)] if key.isdigit() else node[key]
        if value is DELETE:
            del node[int(leaf) if leaf.isdigit() else leaf]
        else:
            node[int(leaf) if leaf.isdigit() else leaf] = value

    return apply


DELETE = object()

REJECTIONS = [
    ("version", 2, "version must be 1"),
    ("template", "other", "template must be"),
    ("repository.id", "no-owner", "OWNER/REPOSITORY"),
    ("repository.layout_status", "chaotic", "layout_status"),
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
    ("governance", DELETE, "must pin"),
    ("governance.repository", "larsbx/elsewhere", "must pin"),
    ("governance.revision", "main", "40-hex"),
    ("governance.sha256", {}, "vendored file set"),
]


@pytest.mark.parametrize(("path", "value", "message"), REJECTIONS, ids=[f"{r[0]}:{r[2]}" for r in REJECTIONS])
def test_each_rule_fails_closed(consumer: Path, path: str, value, message: str):
    data = pinned(consumer)
    mutate(path, value)(data)
    with pytest.raises(AssertionError, match=message):
        audit.validate(data, consumer)


def test_supporting_language_cannot_accept(consumer: Path):
    data = pinned(consumer)
    data["language"].append(
        {"name": "Julia", "authority": "supporting", "roles": ["oracle"],
         "acceptance_authority": True}
    )
    with pytest.raises(AssertionError, match="cannot have acceptance authority"):
        audit.validate(data, consumer)


def test_duplicate_language_is_rejected(consumer: Path):
    data = pinned(consumer)
    data["language"].append(copy.deepcopy(data["language"][0]))
    with pytest.raises(AssertionError, match="duplicate language"):
        audit.validate(data, consumer)


def test_local_edit_of_vendored_file_is_rejected(consumer: Path):
    data = pinned(consumer)
    with (consumer / "tools/audit_estate_layout.py").open("a", encoding="utf-8") as fh:
        fh.write("# local drift\n")
    with pytest.raises(AssertionError, match="digest mismatch"):
        audit.validate(data, consumer)


def test_missing_architecture_entrypoint_is_rejected(consumer: Path):
    (consumer / "ARCHITECTURE.md").unlink()
    with pytest.raises(AssertionError, match="missing architecture entrypoint"):
        audit.validate(pinned(consumer), consumer)


def test_pixi_identity_must_agree(consumer: Path):
    (consumer / "pixi.toml").write_text('[workspace]\nname = "other"\n', encoding="utf-8")
    with pytest.raises(AssertionError, match="pixi workspace identity"):
        audit.validate(pinned(consumer), consumer)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('repository = "larsbx/other"\n[estate]\nmanifest = "estate.toml"\n', "repository disagrees"),
        (f'repository = "{CONSUMER}"\n', "must link to estate.toml"),
    ],
)
def test_polyglot_manifest_must_agree(consumer: Path, body: str, message: str):
    (consumer / "polyglot.manifest.toml").write_text(body, encoding="utf-8")
    with pytest.raises(AssertionError, match=message):
        audit.validate(pinned(consumer), consumer)


def test_governance_source_must_not_pin_itself():
    data = audit.load(ROOT / "estate.toml")
    data["governance"] = baseline()["governance"]
    with pytest.raises(AssertionError, match="source repository must not pin"):
        audit.validate(data, ROOT)


def test_main_reports_failure(consumer: Path, capsys):
    assert audit.main(["--root", str(consumer)]) == 1
    assert "estate-layout audit failed" in capsys.readouterr().err


def test_canonical_layout_requires_every_plane_at_its_target(consumer: Path):
    data = pinned(consumer)
    data["repository"]["layout_status"] = "canonical"
    with pytest.raises(AssertionError, match="canonical layout: plane policy must map its target"):
        audit.validate(data, consumer)


def test_canonical_layout_rejects_glob_mappings(consumer: Path):
    (consumer / "policy").mkdir()
    (consumer / "kernel").mkdir()
    data = pinned(consumer)
    data["repository"]["layout_status"] = "canonical"
    for plane in data["plane"]:
        plane["current"] = [plane["target"]]
    audit.validate(data, consumer)
    data["plane"][1]["current_globs"] = ["kern*"]
    with pytest.raises(AssertionError, match="canonical layout: plane kernel must map its target"):
        audit.validate(data, consumer)


def test_canonical_layout_requires_an_empty_migration_queue(consumer: Path):
    (consumer / "policy").mkdir()
    (consumer / "kernel").mkdir()
    data = pinned(consumer)
    data["repository"]["layout_status"] = "canonical"
    for plane in data["plane"]:
        plane["current"] = [plane["target"]]
    data["migration"] = {"next": ["one more move"]}
    with pytest.raises(AssertionError, match="canonical layout must have no pending migration"):
        audit.validate(data, consumer)
