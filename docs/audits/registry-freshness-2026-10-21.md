# Registry freshness acceptance investigation — 2026-10-21

Base: `ff168c10478d4c12195ac042f56886d38a64a821` (main after PRs #15 and #11).
The current estate has **21** members, rather than the 20 at PR #15.

## Verified baseline and repair

The existing Actions run [39667864091](https://github.com/larsbx/estate-governance/actions/runs/39667864091)
failed the estate-wide invariant audit. A local baseline run had 11 failing
tests, all caused by `llm-kernel-lab` lacking `decided_by`. Its actual manifest
declares `origin.decided_by = "proposed"`; regeneration restores that field.
It remains `candidate`, with no invented adopting decision or stage promotion.

The regenerated registry also advances governance, PSC and llm-kernel-lab source
revisions to the observed heads. Their manifest blobs and adopted positions are
unchanged. The source revisions and all regenerated entries were inspected.

## Source access findings

Anonymous acquisition captured **17** repositories and failed on these four
private repositories. Connected GitHub metadata independently confirmed their
private visibility and `main` refs:

| Repository | Observed `main` (also the existing source revision) |
| --- | --- |
| `finite-julia-set-research` | `ff8a3cd55a5e128fca8213e6eebd7053501b3a58` |
| `closure-fiber-of-multiplication-research` | `3e8266d3e24150e7e3e8dac3b6d956aec76db12a` |
| `giant-fibers-finite-fields-thin-groups` | `8c9675298be7ef79c74eac8ad7bc9a43052f0cdd` |
| `oracles` | `872214c8a0a2b4137bb876427bebfac6b46bb6e7` |

The anonymous acquisition returned failure and wrote an **incomplete** receipt.
Those failed sources were not omitted or replaced with old rows.

For additional **local-only** validation, the connected GitHub API supplied the
four exact commit objects, relevant trees, manifests and workflows. Reconstructed
Git object hashes were verified against every API object ID. Each observed head
equals its recorded source, so this evidence establishes identity, not a claim
about unavailable intervening history. Private source contents were not added
to this public repository.

The resulting explicitly assembled local evidence capture combined those four
API observations with the 17 Git observations. After reviewed regeneration,
its receipt was explicitly rebound to the regenerated source pins using their
verified Git objects. This was a replay of captured observations, **not a fresh
network acquisition**. The freshness checker passed all 21 rows on that capture;
the original byte-for-byte snapshot `--check` also passed all 21. This local
evidence does not confer private-source access on GitHub Actions.

## Local validation

- Full Python suite: 168 tests, including 33 acquisition/freshness tests.
- Repository architecture audit: passed.
- Estate-wide registry invariant audit: passed (21 members).
- Generated adopter table check: passed.
- Snapshot regeneration/check at captured exact refs: passed.
- Freshness replay on the explicitly assembled connected capture: passed.
- Anonymous live acquisition against the real estate: **failed** (the four
  inaccessible private repositories above).

Negative fixtures use local Git repositories and no network. They reject
manifest-byte drift, a removed CI gate, forged/altered row fields, unknown or
non-ancestral source commits, missing repositories/branches/manifests/objects,
changed observed revisions, inconsistent receipts, membership omissions and
duplicates, header inconsistency, and reuse of an acquisition directory. They
also demonstrate that unrelated code changes and governance's committed PR
HEAD do not cause a self-reference loop.

## Hosted acceptance and remaining requirement

The workflow includes an independent, unconditional **Registry snapshot
freshness** job on PRs and main pushes, plus manual dispatch. It uses only
read permissions and uploads a receipt even on acquisition failure. It has no
private cross-repository credential, fallback, or success-on-skip path.

**Hosted acceptance is blocked pending a trusted read-only acquisition path to
the four private repositories.** No hosted freshness pass is claimed here. The
PR must retain the failing gate and remain unmerged until access is configured
and the exact proposed head passes both workflow jobs. If a hosted run cannot
start because of billing or permissions, that is a separate blocker and must
be recorded as such.

The connected integration returned 403 when reading main's branch protection;
this investigation therefore does not claim that the new check is already
configured as a required status check. Require `test` and `Registry snapshot
freshness` in the repository's acceptance settings when enabling the gate.
Normal operator review remains the authority for integration.
