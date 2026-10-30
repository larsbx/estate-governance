# Registry snapshot freshness v1

The acceptance workflow runs both the existing estate-wide invariant audit and
**Registry snapshot freshness**. A valid graph alone does not establish that
the registry still describes its sources. This check does not promote stages,
adopt positions, or change domain acceptance authority.

## Freshness policy: `manifest-current-v1`

For every member, including archived members:

1. Capture `refs/heads/main` from its declared `larsbx/<id>` GitHub repository.
   Each repository is observed separately, once; this is not an atomic estate
   transaction. The receipt records each exact commit and observation time.
2. Require the recorded `source_commit` to exist in that repository and be an
   ancestor of the observed commit. Require its manifest blob, identity, and
   every derived registry field to reproduce exactly. A plausible hexadecimal
   revision alone is insufficient. Unknown/non-generated row fields also fail.
3. Require the manifest **bytes** at the observed commit to have the same Git
   blob as the recorded source, and require all generated facts other than
   `source_commit` to agree. Even a manifest comment change requires refresh.
   The `ci_gate` projection is recomputed from the committed workflow files at
   both commits. The receipt records all workflow blob IDs at both revisions.

An unrelated code commit does not force a registry update. The recorded commit
remains the exact source of the row; the receipt distinguishes it from the
newer observed head. Workflow changes require a registry update when they change
the generated `ci_gate` fact. That fact retains the existing generator's textual
test for `audit_estate_layout.py`; it does not prove the workflow executes the
audit successfully or cover branch-protection configuration.

For **estate-governance itself**, use the exact proposed PR head (or pushed
commit) selected by the acceptance workflow rather than remote `main`. The
credentialled job imports this commit as Git data while its executable checkout
remains at an immutable, independently reviewed acquisition revision. Local
commands default to committed `HEAD`. A registry
cannot contain its own eventual commit ID. A preceding reachable commit with
identical manifest bytes and generated facts is therefore valid for this row
too. Uncommitted worktree files are never substituted for committed evidence.

There is no maximum snapshot age when these conditions hold. "Fresh" means
current at the captured heads, not necessarily at a later merge instant. Rerun
CI after source changes; a passing historical run is not a perpetual freshness
claim. Normal PR review controls changes to membership and to this policy.

## Acquisition and access

```sh
# Use a new directory for each live observation. Full-history governance checkout required.
python tools/check_registry_freshness.py --fetch --sources /tmp/estate-observation-1

# Replay the same receipt and materialized Git objects, with no new observation.
python tools/check_registry_freshness.py --sources /tmp/estate-observation-1
```

The acquisition path uses fresh **bare** repositories, fixed GitHub HTTPS URLs,
an explicit `main` ref, full commit ancestry, and partial blob fetching. It reads
only the committed manifest and workflows; it never checks out member trees,
runs hooks from members, recurses into submodules, or executes their code. After
materializing the required blobs it disables lazy fetching for local replay.
Git replacement objects are disabled. Four concurrent fetches limit resource
use. An existing capture directory is rejected rather than treated as a cache.

The hosted acceptance path authenticates every remote member acquisition with
an installation token explicitly requesting only `contents: read` over the
registered source repositories. The repository's ordinary `GITHUB_TOKEN` does
not confer cross-repository private access. No token is persisted by checkout,
written into Git configuration, or passed to the unprivileged test job. The
local `check_registry_freshness.py --fetch` command remains an explicit anonymous
diagnostic; it is **not** the hosted acceptance path.
If a member becomes private/inaccessible, fails to supply `main` or
`ESTATE.toml`, has an unavailable revision, or fetches time out, acquisition
fails and records an incomplete receipt. There is no fallback to stale local
data, cached registry rows, another branch, or omission of the member.

`registry_source_access.py` verifies the installation's exact repository scope
before acquiring anything. Missing/invalid credentials or scope produce a
configuration failure; a failed Git fetch is never retried anonymously. The
candidate must have the same membership as the trusted acquisition revision.
Membership changes require updating that reviewed revision and App selection.
The token is supplied only in process-local, URL-scoped HTTP headers; inherited
Git configuration, credential helpers, redirects, hooks and trace output are
disabled. Public receipts suppress transport diagnostics. Only the receipt is
uploaded; private Git objects and manifest/workflow contents stay on the runner.

Credential release requires the protected `registry-source-read` environment
and approval of the exact run/workflow by a required reviewer. The acquisition
code is pinned to a full commit, reads the candidate registry with `git show`,
and never checks out or executes candidate code. Fork PR acquisition is refused
and the final acceptance job fails on skipped/cancelled/failed acquisition.
There is no `pull_request_target` execution or success-on-skip path.

**Configuration is an acceptance prerequisite, not something a workflow file
can establish.** Do not supply the App key until the environment protections
described in [source credential setup](registry-source-credentials-v1.md) are
configured and verified. Do not resolve the private-source P1 until hosted
authenticated verification succeeds on the exact candidate.

References: [checkout history, credential and private-repository guidance](https://github.com/actions/checkout),
[GitHub token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication).

## Refresh and review

On detected drift, use the captured immutable refs to regenerate, then review
the complete registry and adopter diff:

```sh
python tools/snapshot_registry.py --sources /tmp/estate-observation-1 --ref refs/heads/estate-observed
python tools/render_adopters.py
python kernel/audit_estate_layout.py
python kernel/audit_estate_registry.py
python tools/render_adopters.py --check
python -m pytest
```

Commit the generated changes and acquire a **new** observation for acceptance.
A receipt binds the registry's source revisions; it cannot be silently reused
after a pin change. If a recorded source revision is invalid/unavailable,
acquisition fails; repair it explicitly under PR review rather than treating a
new head as evidence for the old row. Adopted position changes still require
the existing decision-record process.

The original `snapshot_registry.py --check` remains a stricter byte-for-byte
comparison with newly generated head snapshots. It can report drift on
unrelated code commits that `manifest-current-v1` intentionally permits.

## Evidence and acceptance

The acquisition job always attempts to upload its public receipt, including
configuration and acquisition failures, as `registry-source-observation` for
30 days. A successful receipt names
every member, its source revision, observed revision, manifest blobs and
workflow blobs, the tested revision, verified authentication scope and the
validation verdict. Missing member fields (including observation time) or
missing error evidence fail replay. Replaying the local capture is deterministic; fetching the
immutable revisions again depends on their continued availability at GitHub.
The receipt is not an independent attestation or a permanent source archive.

The test job and final freshness acceptance job must succeed. The latter runs
with `always()` and requires its acquisition dependency to have succeeded; a
skip is a failure. It has no `continue-on-error` or dependency on the test job
that would hide its result when another gate fails. Branch protection should require
`test` and `Registry snapshot freshness`; writing a workflow does not configure
those settings. Administrative write access may still bypass operator checks.

Permissions failures, unavailable repositories, billing restrictions, queued or
unexecuted jobs must be reported as blockers, never as passing validation.
