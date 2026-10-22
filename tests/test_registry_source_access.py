from __future__ import annotations

import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
import subprocess
import threading
from urllib.error import HTTPError

import pytest

import check_registry_freshness as fresh
import registry_source_access as access
import snapshot_registry as snap
from test_registry_freshness import commit, estate  # reuse real Git estate fixture


def test_process_auth_is_scoped_ephemeral_and_has_no_helper_fallback(monkeypatch):
    monkeypatch.setenv("GIT_TRACE_CURL", "1")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "untrusted inherited config")
    monkeypatch.setenv("ESTATE_SOURCE_TOKEN", "secret-test-value")
    before = dict(os.environ)
    with access.authenticated_git("secret-test-value", ["larsbx/demo"]):
        env = dict(os.environ)
        assert "GIT_TRACE_CURL" not in env and "ESTATE_SOURCE_TOKEN" not in env
        config = {env[f"GIT_CONFIG_KEY_{i}"]: env[f"GIT_CONFIG_VALUE_{i}"]
                  for i in range(int(env["GIT_CONFIG_COUNT"]))}
        assert config["credential.helper"] == ""
        assert config["http.followRedirects"] == "false"
        assert config["protocol.allow"] == "never"
        headers = [k for k in config if k.endswith(".extraheader")]
        assert headers == ["http.https://github.com/larsbx/demo.git.extraheader"]
        assert config[headers[0]].endswith(base64.b64encode(b"x-access-token:secret-test-value").decode())
    assert dict(os.environ) == before


@pytest.mark.parametrize("token", ["", "bad\nheader", "bad token"])
def test_missing_or_malformed_token_is_rejected_before_network(token, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("missing credentials must not attempt anonymous access")
    monkeypatch.setattr(access, "urlopen", no_network)
    with pytest.raises(fresh.FreshnessError, match="CONFIGURATION"):
        access.validate_installation_scope(token, ["larsbx/demo"])


@pytest.mark.parametrize("status", [401, 403, 404])
def test_invalid_credentials_or_inaccessible_installation_never_fall_back(status, monkeypatch):
    calls = []

    def denied(request, **kwargs):
        calls.append(request)
        raise HTTPError(request.full_url, status, "secret-test-value", {}, io.BytesIO(b"secret-test-value"))

    monkeypatch.setattr(access, "urlopen", denied)
    with pytest.raises(fresh.FreshnessError, match=f"HTTP {status}") as error:
        access.validate_installation_scope("secret-test-value", ["larsbx/demo"])
    assert "secret-test-value" not in str(error.value)
    assert len(calls) == 1
    assert calls[0].get_header("Authorization") == "Bearer secret-test-value"


@pytest.mark.parametrize("names,total", [([], 0), (["larsbx/wrong"], 1),
                                        (["larsbx/demo", "larsbx/extra"], 2),
                                        (["larsbx/demo", "larsbx/demo"], 2),
                                        (["larsbx/demo"], 100)])
def test_missing_extra_duplicate_or_paginated_scope_fails(names, total, monkeypatch):
    response = {"total_count": total, "repositories": [{"full_name": name} for name in names]}
    monkeypatch.setattr(access, "urlopen", lambda *a, **kw: io.BytesIO(json.dumps(response).encode()))
    with pytest.raises(fresh.FreshnessError, match="CONFIGURATION"):
        access.validate_installation_scope("test-token", ["larsbx/demo"])


def test_exact_installation_scope_passes(monkeypatch):
    response = {"total_count": 1, "repositories": [{"full_name": "larsbx/demo"}]}
    monkeypatch.setattr(access, "urlopen", lambda *a, **kw: io.BytesIO(json.dumps(response).encode()))
    access.validate_installation_scope("test-token", ["larsbx/demo"])


def write_candidate(data, origins):
    gov = origins["estate-governance"]
    registry = gov / "policy/estate-registry.toml"
    registry.parent.mkdir(exist_ok=True)
    registry.write_text(snap.render({k: data[k] for k in ("governance_source_commit", "required_audit_revision")},
                                   data["member"]))
    return commit(gov, "candidate registry")


def test_candidate_is_data_and_does_not_change_executed_checkout(estate):
    data, origins, _ = estate
    revision = write_candidate(data, origins)
    gov = origins["estate-governance"]
    snap.git(gov, "checkout", "HEAD^")
    executable_revision = snap.git(gov, "rev-parse", "HEAD").strip()
    assert access.candidate_data(gov, revision, data) == data
    assert snap.git(gov, "rev-parse", "HEAD").strip() == executable_revision != revision


@pytest.mark.parametrize("revision", ["main", "HEAD", "f" * 40, "--all", "../main"])
def test_unavailable_or_mutable_candidate_is_rejected(estate, revision):
    data, origins, _ = estate
    with pytest.raises((fresh.FreshnessError, subprocess.CalledProcessError)):
        access.candidate_data(origins["estate-governance"], revision, data)


def test_candidate_cannot_expand_or_remove_credential_scope(estate):
    data, origins, _ = estate
    revision = write_candidate(data, origins)
    trusted = {**data, "member": data["member"][:1]}
    with pytest.raises(fresh.FreshnessError, match="membership"):
        access.candidate_data(origins["estate-governance"], revision, trusted)


def test_ref_race_is_rejected_before_reading_candidate(estate, monkeypatch):
    data, origins, _ = estate
    def moved(repo, *args):
        if args[0] == "fetch":
            return ""
        if args[0] == "rev-parse":
            return "f" * 40
        pytest.fail("must fail before reading candidate bytes")

    monkeypatch.setattr(snap, "git", moved)
    with pytest.raises(fresh.FreshnessError, match="moved"):
        access.prepare_candidate(origins["estate-governance"], "a" * 40, 16, data)


def test_authenticated_git_error_never_exposes_transport_diagnostics(estate, monkeypatch):
    _, origins, _ = estate

    def denied(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0], stderr="AUTHORIZATION secret-test-value")

    monkeypatch.setattr(subprocess, "run", denied)
    with access.authenticated_git("secret-test-value", ["larsbx/demo"]):
        with pytest.raises(subprocess.CalledProcessError) as error:
            snap.git(origins["demo"], "fetch", "origin")
    assert "secret-test-value" not in fresh.describe_error(error.value)


def test_missing_configuration_produces_failure_receipt(estate, tmp_path, monkeypatch):
    data, origins, sources = estate
    revision = write_candidate(data, origins)
    monkeypatch.setattr(snap, "ROOT", origins["estate-governance"])
    monkeypatch.setattr(snap, "REGISTRY", origins["estate-governance"] / "policy/estate-registry.toml")
    monkeypatch.delenv("ESTATE_SOURCE_TOKEN", raising=False)
    path = tmp_path / "public-receipt.json"
    assert access.main(["verify", "--candidate", revision, "--sources", str(sources),
                        "--receipt", str(path)]) == 1
    receipt = json.loads(path.read_text())
    assert receipt["complete"] is False
    assert "CONFIGURATION" in receipt["errors"][0]
    assert receipt["tested_revision"] == revision
    assert not sources.exists()


def test_authenticated_capture_checks_candidate_revision_and_full_evidence(estate, tmp_path, monkeypatch):
    data, origins, sources = estate
    revision = write_candidate(data, origins)
    gov = origins["estate-governance"]
    monkeypatch.setattr(snap, "ROOT", gov)
    monkeypatch.setattr(snap, "REGISTRY", gov / "policy/estate-registry.toml")
    monkeypatch.setenv("ESTATE_SOURCE_TOKEN", "test-token")
    monkeypatch.setattr(access, "validate_installation_scope", lambda *args: None)
    path = tmp_path / "public-receipt.json"
    assert access.main(["verify", "--candidate", revision, "--sources", str(sources),
                        "--receipt", str(path)]) == 0
    receipt = json.loads(path.read_text())
    assert receipt["authentication"] == {"scheme": access.AUTH_SCHEME, "repositories": ["larsbx/demo"]}
    assert receipt["validation"] == {"passed": True, "errors": []}
    assert receipt["member"][0]["commit"] == revision
    assert "test-token" not in path.read_text()
    assert fresh.check(data, sources, receipt, "f" * 40)


@contextmanager
def git_server(root=None):
    # Real Git HTTP requests exercise credential handling, not a mocked fetch.
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.headers.get("Authorization"))
            expected = "basic " + base64.b64encode(b"x-access-token:valid-test-token").decode()
            if root is None or self.headers.get("Authorization", "").lower() != expected.lower():
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="private source"')
                self.end_headers()
                return
            self.serve_git()

        def do_POST(self):
            self.do_GET()

        def serve_git(self):
            path, _, query = self.path.partition("?")
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            env = {**os.environ, "GIT_PROJECT_ROOT": str(root), "GIT_HTTP_EXPORT_ALL": "1",
                   "PATH_INFO": path, "QUERY_STRING": query, "REQUEST_METHOD": self.command,
                   "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                   "CONTENT_LENGTH": str(len(body)), "REMOTE_USER": "app-installation"}
            result = subprocess.run(["git", "http-backend"], input=body, capture_output=True,
                                    env=env, check=True, timeout=10).stdout
            headers, _, content = result.partition(b"\r\n\r\n")
            self.send_response(200)
            for line in headers.decode().splitlines():
                key, value = line.split(":", 1)
                self.send_header(key, value.strip())
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, requests
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def http_environment(token, url):
    env = access.git_environment(token, ["larsbx/demo"])
    for i in range(int(env["GIT_CONFIG_COUNT"])):
        if env[f"GIT_CONFIG_KEY_{i}"].endswith(".extraheader"):
            env[f"GIT_CONFIG_KEY_{i}"] = f"http.{url}.extraheader"
    count = int(env["GIT_CONFIG_COUNT"])
    env.update({"GIT_CONFIG_COUNT": str(count + 1), f"GIT_CONFIG_KEY_{count}": "protocol.http.allow",
                f"GIT_CONFIG_VALUE_{count}": "always"})
    return env


def test_real_http_git_rejection_never_retries_anonymously_or_persists_token(tmp_path):
    repo = tmp_path / "bare.git"
    snap.git(tmp_path, "init", "--bare", str(repo))
    with git_server() as (server, requests):
        url = f"http://127.0.0.1:{server.server_port}/demo.git"
        env = http_environment("invalid-test-token", url)
        result = subprocess.run(["git", "-C", str(repo), "fetch", url, "refs/heads/main"],
                                env=env, text=True, capture_output=True, timeout=10)
    expected = "basic " + base64.b64encode(b"x-access-token:invalid-test-token").decode()
    assert result.returncode != 0
    assert requests and all(header.lower() == expected.lower() for header in requests)
    assert "invalid-test-token" not in result.stdout + result.stderr
    assert "extraheader" not in (repo / "config").read_text()
    assert "invalid-test-token" not in (repo / "config").read_text()


def test_real_authenticated_http_fetch_retains_immutable_revision(estate, tmp_path):
    data, origins, _ = estate
    repo = tmp_path / "http-capture.git"
    snap.git(tmp_path, "init", "--bare", str(repo))
    with git_server(origins["demo"].parent) as (server, requests):
        url = f"http://127.0.0.1:{server.server_port}/demo"
        result = subprocess.run(["git", "-C", str(repo), "fetch", "--no-tags", url,
                                 f"refs/heads/main:{fresh.REF}"],
                                env=http_environment("valid-test-token", url),
                                text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert requests and None not in requests
    assert snap.git(repo, "rev-parse", fresh.REF).strip() == data["member"][1]["source_commit"]
    assert snap.snapshot(repo, fresh.REF) == data["member"][1]
    assert "extraheader" not in (repo / "config").read_text()
