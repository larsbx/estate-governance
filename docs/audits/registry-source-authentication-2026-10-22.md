# Registry source authentication repair — 2026-10-22

## Verified starting point

PR #16 remained open at `23e2e0a07bcf2042e707ab4985acc227baa6c0c0` with
unresolved P1 [review comment 4342083580](https://github.com/larsbx/estate-governance/pull/16#discussion_r4342083580).
The existing [hosted run 39677568871](https://github.com/larsbx/estate-governance/actions/runs/39677568871)
passed tests but failed anonymous acquisition for all four private members.
Local connected-account evidence is not an Actions credential or hosted pass.

## Implemented correction

The workflow pins acquisition tools to the full immutable commit
`2d91af29ad4e8f8fbcfcca7b30cb3e8a330e9254`. That tool commit must receive
operator review before its first credentialled approval. The job reads the
exact proposed head as Git data, independently verifies App installation scope,
and authenticates all 20 remote sources with a Contents-read installation token.
The 21st member, estate-governance, is observed at the exact proposed commit.
No candidate executable, action, workflow or test runs in the credentialled job.

Credential release depends on the protected `registry-source-read` environment.
The test job has no cross-repository credentials. Fork acquisition is refused;
the stable final freshness job fails on skipped/cancelled/failed acquisition.
Token transport uses process-local, source-URL-scoped HTTP headers, no helpers,
redirects, stored Git credentials, trace output or anonymous fallback. The App
action revokes the token in its post step. Only the public receipt is uploaded,
never private Git objects or source-file contents.

The source revision, ancestry, manifest, workflow inputs, generated rows and
manifest-current policy remain mandatory. Incomplete receipts, including missing
timestamps or error evidence, fail replay. No authority, adoption, stage or
registry-governance rule is relaxed.

## Validation and remaining prerequisites

At the implementation checkpoint:

- 202 local Python tests pass; estate-layout/registry audits and adopter rendering pass.
- Real HTTP Git regressions verify successful header-authenticated fetching at
  the exact revision and failed authentication without an anonymous retry or
  stored credentials. These are local fixtures, not GitHub App access proof.
- Deterministic tests cover inaccessible repositories, invalid credentials and
  installation scope, ref races, wrong/unavailable revisions, omitted evidence,
  secret suppression, and separation of executable checkout from candidate data.
- Hosted authenticated success has **not** been established. No App key,
  environment configuration, required reviewer or branch-protection setting is
  claimed to exist. The connected GitHub tools do not expose App creation,
  environment/secret administration or environment approval capabilities.

Use [the operator setup](../architecture/registry-source-credentials-v1.md) to
configure the dedicated read-only App and environment, then approve and run the
exact current candidate. Record its run URL, SHA and full receipt on PR #16.
Keep the P1 unresolved and PR unmerged until authenticated hosted acceptance and
the existing test/audit job succeed. A configuration failure is evidence of an
unmet prerequisite; it is not an authenticated pass or grounds to weaken the gate.
