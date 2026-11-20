#!/usr/bin/env python3
"""Execute both formal lanes and record source-bound, scoped evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
LEAN_TOOLCHAIN = "leanprover/lean4:v4.34.1"
LEAN_COMMIT = "5045d0056413266e57c625dcd7c365b10e377c52"
QUINT_TOOLCHAIN = "@informalsystems/quint@0.33.1"
SEED = "20261120"
REQUIRED_LEAN = {
    "EstateFormal.ready_requires_both", "EstateFormal.stale_lean_source_not_ready",
    "EstateFormal.stale_quint_policy_not_ready", "EstateFormal.revise_source_invalidates",
    "EstateFormal.revise_policy_invalidates", "EstateFormal.transition_preserves_verified",
    "EstateFormal.reachable_verified_requires_both", "EstateFormal.transition_preserves_authority",
    "EstateFormal.reachable_preserves_authority",
}
AUDITED_LEAN = REQUIRED_LEAN | {
    "EstateFormal.ready_requires_same_source", "EstateFormal.ready_requires_same_policy",
    "EstateFormal.nonpassed_lean_not_ready", "EstateFormal.nonpassed_quint_not_ready",
    "EstateFormal.record_lean_invalidates", "EstateFormal.record_quint_invalidates",
    "EstateFormal.initial_safe", "EstateFormal.verification_does_not_grant_authority",
}
QUINT_TESTS = {
    "missingEvidenceTest", "bothChecksTest", "singleLaneTest", "staleSourceTest",
    "stalePolicyTest", "failedResultTest", "queuedResultTest", "authorityPreservedTest",
    "recoveryRequiresBothFreshResultsTest",
}
REQUIRED_QUINT = (QUINT_TESTS - {"recoveryRequiresBothFreshResultsTest"}) | {"safety"}
SKIP_DIRS = {".git", ".lake", ".pytest_cache", "__pycache__", "node_modules", "build", "dist"}
SKIP_SUFFIXES = {".pyc", ".olean", ".ilean"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def source_snapshot(root: Path) -> tuple[list[dict], str]:
    files = []
    excluded_evidence = root / "formal/evidence"

    def fail_walk(error: OSError) -> None:
        raise error

    for parent, directories, names in os.walk(root, onerror=fail_walk):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS
                                and Path(parent) / name != excluded_evidence)
        for name in directories:
            if (Path(parent) / name).is_symlink():
                raise ValueError("source directory symlinks are outside the receipt contract")
        for name in sorted(names):
            path = Path(parent) / name
            if name == ".git" or path.suffix in SKIP_SUFFIXES:
                continue
            if path.is_symlink():
                raise ValueError("source file symlinks are outside the receipt contract")
            content = path.read_bytes()
            files.append({"path": path.relative_to(root).as_posix(), "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest()})
    files.sort(key=lambda row: row["path"])
    return files, canonical_digest(files)


def local_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("formal input must be a repository-relative path")
    path = Path(value)
    if path.is_absolute() or any(part in (".", "..") for part in value.split("/")):
        raise ValueError("formal input must remain inside the repository")
    actual = root / path
    if actual.is_symlink() or not actual.is_file() or not actual.resolve().is_relative_to(root):
        raise ValueError(f"missing or escaping formal input: {value}")
    return actual


def configuration(root: Path) -> dict:
    manifest = tomllib.loads((root / "ESTATE.toml").read_text())
    if manifest.get("version") != 3 or manifest.get("template") != "estate-repository-v3":
        raise ValueError("this formal gate requires estate-repository-v3")
    spec = manifest["formalization"]
    if spec["gate"] != "tools/check_formal.py":
        raise ValueError("manifest does not name this formal gate")
    local_path(root, spec["scope"])
    if not spec["implementation_paths"]:
        raise ValueError("formalization implementation paths cannot be empty")
    for value in spec["implementation_paths"]:
        local_path(root, value)
    for lane, toolchain, sources, required, supported in [
        ("lean", LEAN_TOOLCHAIN, {"formal/lean/EstateFormal.lean", "formal/lean/Audit.lean"},
         REQUIRED_LEAN, AUDITED_LEAN),
        ("quint", QUINT_TOOLCHAIN, {"formal/quint/EstateFormal.qnt"},
         REQUIRED_QUINT, QUINT_TESTS | {"safety"}),
    ]:
        row = spec[lane]
        if row["toolchain"] != toolchain or set(row["sources"]) != sources:
            raise ValueError(f"{lane}: declared inputs or toolchain differ from this gate")
        obligations = row["obligations"]
        if len(obligations) != len(set(obligations)) or not required <= set(obligations) <= supported:
            raise ValueError(f"{lane}: declared obligations differ from the executed inventory")
        for source in sources:
            local_path(root, source)
    if (root / "formal/lean/lean-toolchain").read_text().strip() != LEAN_TOOLCHAIN:
        raise ValueError("Lean toolchain file differs from manifest")
    package = json.loads((root / "formal/quint/package.json").read_text())
    if package["dependencies"].get("@informalsystems/quint") != "0.33.1":
        raise ValueError("Quint package differs from manifest")
    lock = json.loads((root / "formal/quint/package-lock.json").read_text())
    if lock["packages"]["node_modules/@informalsystems/quint"]["version"] != "0.33.1":
        raise ValueError("Quint lock differs from manifest")
    return spec


def executable(name: str) -> Path:
    found = shutil.which(name)
    if found is None:
        raise ValueError(f"missing executable: {name}")
    # Preserve argv[0] for dispatching shims such as elan's lean command.
    return Path(found).absolute()


def declared_inputs(spec: dict) -> list[str]:
    paths = ["ESTATE.toml", spec["scope"], spec["gate"],
             *spec["implementation_paths"], *spec["lean"]["sources"], *spec["quint"]["sources"],
             "formal/lean/lean-toolchain", "formal/quint/package.json", "formal/quint/package-lock.json"]
    return sorted({Path(path).as_posix() for path in paths})


def validate_declared_inputs(root: Path, files: list[dict]) -> list[str]:
    paths = declared_inputs(configuration(root))
    covered = {row["path"] for row in files}
    for path in paths:
        if path not in covered:
            raise ValueError(f"declared input is excluded from the source digest: {path}")
    return paths


def run_command(command: list[str], cwd: Path, output: Path, receipt: dict,
                name: str, *, env: dict | None = None, expected_failure: bool = False) -> str:
    record = {"name": name, "command": command, "command_sha256": canonical_digest(command),
              "cwd": str(cwd), "started_at_utc": now()}
    if env is not None:
        record["lean_path"] = env.get("LEAN_PATH")
    receipt["commands"].append(record)
    save(output / "results.json", receipt)
    try:
        result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=300)
        text = result.stdout + result.stderr
        record["exit_code"] = result.returncode
    except (OSError, subprocess.TimeoutExpired) as error:
        text = f"{type(error).__name__}: {error}\n"
        record.update(exit_code=None, execution_error=type(error).__name__)
    logfile = output / f"{name}.log"
    logfile.write_text(text)
    record.update(finished_at_utc=now(), log=logfile.name, log_sha256=sha256(logfile))
    save(output / "results.json", receipt)
    if record["exit_code"] is None or (not expected_failure and record["exit_code"] != 0):
        raise RuntimeError(f"{name} failed; see {logfile}")
    print(f"{name}: exit {record['exit_code']}", flush=True)
    return text


def require_counterexample(record: dict, text: str, trace_path: Path) -> None:
    if record["exit_code"] != 1 or "[violation] Found an issue" not in text \
            or "error: Invariant violated" not in text:
        raise RuntimeError("unsafe verification control did not produce the designated invariant failure")
    trace = json.loads(trace_path.read_text())
    states = trace.get("states", [])
    if len(states) != 2:
        raise RuntimeError("unsafe verification control did not record the expected two-state witness")
    before, after = states[0]["s"], states[1]["s"]
    if before["verified"] is not False or after["verified"] is not True \
            or after["lean"]["result"] != "missing" or after["quint"]["result"] != "missing" \
            or after["domainAuthority"] is not False:
        raise RuntimeError("unsafe verification trace is not the declared missing-evidence counterexample")


def tool_fingerprint(lean: Path, quint: Path, node: Path) -> list[dict]:
    return [{"tool": name, "path": str(path), "sha256": sha256(path)}
            for name, path in (("lean", lean), ("quint_cli", quint), ("node", node))]


def execute_checks(root: Path, output: Path, receipt: dict) -> None:
    receipt["formalization"] = configuration(root)
    lean = executable(os.environ.get("LEAN", "lean"))
    default_quint = root / "formal/quint/node_modules/.bin/quint"
    quint = executable(os.environ.get("QUINT", str(default_quint)))
    node = executable("node")
    lean_version = run_command([str(lean), "--version"], root, output, receipt, "lean-version").strip()
    if "version 4.34.1," not in lean_version or LEAN_COMMIT not in lean_version:
        raise RuntimeError("Lean executable version/revision differs from the declared pin")
    quint_version = run_command([str(quint), "--version"], root, output, receipt, "quint-version").strip()
    if quint_version != "0.33.1":
        raise RuntimeError("Quint executable version differs from the declared pin")
    node_version = run_command([str(node), "--version"], root, output, receipt, "node-version").strip()
    receipt["toolchains"] = {"lean": lean_version, "quint": quint_version, "node": node_version,
                             "quint_backend": "typescript", "files": tool_fingerprint(lean, quint, node)}
    with tempfile.TemporaryDirectory(prefix="estate-formal-") as folder:
        build = Path(folder)
        for name in ("EstateFormal.lean", "Audit.lean"):
            shutil.copyfile(root / "formal/lean" / name, build / name)
        env = dict(os.environ, LEAN_PATH=str(build))
        run_command([str(lean), "-o", str(build / "EstateFormal.olean"), "EstateFormal.lean"],
                    build, output, receipt, "lean-build", env=env)
        audit = run_command([str(lean), "Audit.lean"], build, output, receipt, "lean-axiom-audit", env=env)
        if "17 required theorems without axioms" not in audit or "Estate formal axiom audit passed:" not in audit:
            raise RuntimeError("Lean axiom audit did not report its complete required inventory")
        receipt["lean"] = {"status": "passed", "required_theorems": sorted(AUDITED_LEAN),
                           "required_theorem_axioms": [], "namespace_support_axiom_allowlist": ["propext"],
                           "compiled_model_sha256": sha256(build / "EstateFormal.olean")}
    cwd = root / "formal/quint"
    run_command([str(quint), "typecheck", "EstateFormal.qnt"], cwd, output, receipt, "quint-typecheck")
    tests = run_command([str(quint), "test", "EstateFormal.qnt", "--backend=typescript", "--max-samples=1",
                         f"--seed={SEED}"], cwd, output, receipt, "quint-tests")
    if "9 passing" not in tests or any(f"ok {name} passed 1 test(s)" not in tests for name in QUINT_TESTS):
        raise RuntimeError("Quint did not execute the complete deterministic obligation inventory")
    simulation = run_command([str(quint), "run", "EstateFormal.qnt", "--backend=typescript", "--invariant=safety",
                              "--max-samples=1000", "--max-steps=40", f"--seed={SEED}", "--verbosity=1"],
                             cwd, output, receipt, "quint-bounded-run")
    if "[ok] No violation found" not in simulation:
        raise RuntimeError("Quint bounded run did not report a completed invariant check")
    trace_path = output / "quint-negative.itf.json"
    trace_path.unlink(missing_ok=True)
    negative = run_command([str(quint), "run", "EstateFormal.qnt", "--backend=typescript", "--step=unsafeStep",
                            "--invariant=safety", "--max-samples=1", "--max-steps=1", f"--seed={SEED}",
                            "--verbosity=2", "--out-itf", str(trace_path)],
                           cwd, output, receipt, "quint-negative-control", expected_failure=True)
    require_counterexample(receipt["commands"][-1], negative, trace_path)
    receipt["quint"] = {"status": "passed", "deterministic_tests": sorted(QUINT_TESTS),
                        "invariant": "safety", "backend": "typescript", "seed": SEED,
                        "max_samples": 1000, "max_steps": 40, "unbounded_proof": False,
                        "negative_control": {"step": "unsafeStep", "expected_exit_code": 1,
                                             "trace": trace_path.name, "sha256": sha256(trace_path),
                                             "witnessed": True}}
    after = tool_fingerprint(lean, quint, node)
    receipt["tool_executables_unchanged"] = after == receipt["toolchains"]["files"]
    if not receipt["tool_executables_unchanged"]:
        raise RuntimeError("formal executable identity changed during verification")


def verify(root: Path, output: Path) -> int:
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root) and not output.is_relative_to(root / "formal/evidence"):
        raise ValueError("evidence must be under formal/evidence or outside the repository")
    output.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "estate.formal-evidence.v1", "status": "running", "started_at_utc": now(),
               "evidence_only": True, "domain_acceptance_authority": False,
               "implementation_correspondence": "unproved", "hosted_job_conclusion_included": False,
               "scope": "abstract formal-evidence lifecycle; not the Python auditor or estate-wide coverage",
               "source_digest_encoding": "SHA-256 of sorted path/bytes/sha256 records, compact JSON with sorted keys",
               "excluded_directories": sorted(SKIP_DIRS | {"formal/evidence"}),
               "excluded_suffixes": sorted(SKIP_SUFFIXES), "commands": []}
    # Invalidate prior success before reading configuration, sources or tools.
    save(output / "results.json", receipt)
    try:
        files, digest = source_snapshot(root)
        receipt.update(source_tree_sha256=digest, source_manifest="source-manifest.json",
                       policy_sha256=sha256(root / "ESTATE.toml"))
        receipt["declared_inputs"] = validate_declared_inputs(root, files)
        save(output / "source-manifest.json", files)
        save(output / "results.json", receipt)
        execute_checks(root, output, receipt)
        after_files, after_digest = source_snapshot(root)
        after_inputs = validate_declared_inputs(root, after_files)
        receipt["source_unchanged"] = (files == after_files and digest == after_digest
                                       and receipt["declared_inputs"] == after_inputs)
        if not receipt["source_unchanged"]:
            raise RuntimeError("source or policy changed during formal verification")
        receipt["status"] = "passed"
    except (Exception, KeyboardInterrupt) as error:
        receipt.update(status="failed", failure=f"{type(error).__name__}: {error}")
        print(receipt["failure"], file=sys.stderr, flush=True)
    receipt["finished_at_utc"] = now()
    save(output / "results.json", receipt)
    print(f"Formal evidence {receipt['status']}: {output / 'results.json'}", flush=True)
    return 0 if receipt["status"] == "passed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "formal/evidence")
    args = parser.parse_args()
    return verify(ROOT, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
