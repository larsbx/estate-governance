# SchoolOps Chrome installation and CI evidence — 2026-11-27

**Status:** scoped advisory estate update. The installation and self-hosted
release implementation is merged; current source has successful regression and
release-verifier evidence. A retained complete native distribution, production
publication, and managed-device acceptance are not established. **G8 remains
partially demonstrated and open.**

This audit updates the SchoolOps pilot named in
[DR-0005](../decisions/DR-0005-ci-impact-policy-ownership.md) and
[roadmap G8](../../ROADMAP.md#impact-aware-ci). It follows
[DR-0004](../decisions/DR-0004-periodic-contract-conformance-audits.md)'s separation
of reproducibility, freshness, and missing coverage. The paired
[JSON observations](schoolops-chrome-install-2026-11-27.json) retain exact commits,
source blobs and hashes, run attempts, jobs, artifact metadata, retrieval times,
and the distinct API access results. This is an audit record, not a new normative
receipt format or an estate-wide inventory.

## Inspected sources and estate relationship

| Source | Immutable identity |
| --- | --- |
| Governance main inspected | [`b851c92fceb88c8e6f4604664cf975b567ade161`](https://github.com/larsbx/estate-governance/commit/b851c92fceb88c8e6f4604664cf975b567ade161) |
| SchoolOps main inspected | [`09ba1b0a963413d057c2fcaa51861e151f565c74`](https://github.com/larsbx/school-ops/commit/09ba1b0a963413d057c2fcaa51861e151f565c74) |
| Complete SchoolOps source tree | `eb85cee239aef8c080dcc858760d27bbc4bb1888` |
| Chrome component tree | `0f89949e7610a6556a872d84922ae5982cfdd6bb` at `tools/browser/site_scoped_youtube_guard` |

SchoolOps is a **CI pilot and relevant unregistered consumer**. It is absent
from the inspected 21-member historical registry and has no root `ESTATE.toml`
at the inspected main revision. Real Lean and Quint release artifacts are present
and executed, as described below; their existence does not establish adoption of
the estate v3 manifest, membership, stage, or whole-implementation correspondence.
The historical registry and its generated adopter table remain the authority for
their recorded snapshots.

## Merged implementation and corrected historical status

[PR #46](https://github.com/larsbx/school-ops/pull/46) merged as
`74238738bde087e1da42c2859a3cf6610969b217`. Its final head was
`b53542506919b4122d8b79d1f31dabcc2016ddd8`. All four associated workflows eventually
succeeded: [native](https://github.com/larsbx/school-ops/actions/runs/42933442712),
[regression](https://github.com/larsbx/school-ops/actions/runs/42933442741),
[archive](https://github.com/larsbx/school-ops/actions/runs/42933442744), and
[browser](https://github.com/larsbx/school-ops/actions/runs/42933442665). The queued
snapshot still visible in its PR description is historical, not its current
result.

[PR #48](https://github.com/larsbx/school-ops/pull/48) subsequently merged as
`7b359a2f3dc2f8c7d9d9b31667e25d0fd9fe57e8`, with final head
`547b118aac9f366fc8366c9ac83579a21cb84d57`. Its Chrome component tree is identical
to the inspected current main. The [current setup guide](https://github.com/larsbx/school-ops/blob/09ba1b0a963413d057c2fcaa51861e151f565c74/tools/browser/site_scoped_youtube_guard/README.md)
and [release guide](https://github.com/larsbx/school-ops/blob/09ba1b0a963413d057c2fcaa51861e151f565c74/tools/browser/site_scoped_youtube_guard/RELEASE.md)
describe the implemented flow:

1. Prepare the exact extension ZIP and save the school-site configuration.
2. Reopen that package and prepare a signing/publication contract. Private keys
   stay outside the GUI and artifacts.
3. For self-hosting, independently check downloaded HTTPS XML/CRX bytes, signature,
   identity, version, and package binding before exporting a new deployment.
   Web Store confirmation remains an operator attestation.
4. Apply explicit Windows/Linux administrator policy actions, or use the supplied
   macOS MDM/ChromeOS administration routes; verify the resulting device behavior.

PR #48's all-green statement refers to an earlier head, `1f691db...`, and must not
be transferred to its final head. At the final head, the dedicated release
verifier [passed](https://github.com/larsbx/school-ops/actions/runs/43042241458),
while [native](https://github.com/larsbx/school-ops/actions/runs/43042241698) and
[browser](https://github.com/larsbx/school-ops/actions/runs/43042241550) runs hit
Ubuntu dependency-mirror DNS failures. The
[regression plan](https://github.com/larsbx/school-ops/actions/runs/43042241389)
also rejected an unregistered Factorio test module. That registration failure is
historical: the current-main plan and full regression matrix now pass.

## Fresh release verification and its scope

[Release verification run 45973079227](https://github.com/larsbx/school-ops/actions/runs/45973079227),
attempt 1, succeeded at actual checkout
`ac04819ca07f4f63ee1657c2beaa714c8a61dd08`, the head of merged PR #69. Git object
inspection establishes that this head and current main have the **same complete
source tree**, `eb85cee239aef8c080dcc858760d27bbc4bb1888`. The commit identities
remain distinct; this is not described as a new main-push release-verifier run.

| Lane | Executed evidence |
| --- | --- |
| Linux and macOS runtime | 40 release tests and 26 installer tests passed per platform |
| Windows runtime | 40 release tests ran, with two explicitly reported skips; all 26 installer tests passed |
| Linux publication permissions | One additional test exercised publication from a separate server account |
| Lean 4.19.0 | 44 registered theorems compiled and the dependency audit accepted only `propext` |
| Quint 0.33.1 | Safety checked over a successor-closed finite set of 81 states, with eight executable scenarios |
| Cross-language admission | All 256 assignments of eight Boolean observations compared across Python, Lean, and Quint; 53 malformed runtime inputs refused |
| Negative controls | Five controls exercised false propositions, unexpected axioms/placeholders, and unsafe model transitions |

The two Windows skips concern POSIX publication permissions and unprivileged
symlink creation. They are not executed Windows acceptance. Four acceptance-log
and formal-evidence artifacts were returned for this run, with retention through
December 27. They contain test/formal evidence, **not production installer
downloads**.

The [formal scope](https://github.com/larsbx/school-ops/blob/09ba1b0a963413d057c2fcaa51861e151f565c74/tools/browser/site_scoped_youtube_guard/formal/README.md)
proves abstract release invariants and compares the complete small admission
function. It does not prove cryptography, the parser/TLS/filesystem stack, full
runtime refinement, concurrent publisher coordination, Chrome enforcement, or
liveness. Runtime tests use disposable signing and TLS credentials. Neither
lane establishes a production publication or a managed-device rollout.

## Native downloads, browser evidence, and operator documentation

The latest native run returned in the inspected history is
[43048170207](https://github.com/larsbx/school-ops/actions/runs/43048170207) at
`7b359a2f3dc2f8c7d9d9b31667e25d0fd9fe57e8`. Windows x86_64 and macOS arm64 packaging
and packaged self-tests succeeded. Linux ran 168 Python tests with one skip, then
failed to resolve an Ubuntu package mirror while obtaining display dependencies;
its GUI smoke and native build did not execute. This is missing Linux packaging
evidence, not a demonstrated extension-rule failure.

The artifact API now returns **zero native artifacts** for the inspected PR #46,
PR #48 final-head, and PR #48 merge runs. The workflow declares 14-day retention.
Historical upload IDs and architectures are preserved in the JSON record, but
their exact expiry timestamps and deletion cause are unavailable. No GitHub
Releases were returned. These observations do not exclude publication outside
GitHub; they do mean the old Actions links are not available installer downloads.

The later [browser run 43303535201](https://github.com/larsbx/school-ops/actions/runs/43303535201)
passed 163 actual HTTPS fixture request cases and eight separately labeled
hypothetical DNR probes. It is associated with still-open
[operator-documentation PR #53](https://github.com/larsbx/school-ops/pull/53) at
`f07451cee7e8a9b9bb6435fefbe63089af4cded4`. Its executable Chrome component files
and browser workflow match current main, while six documentation files differ.
This supports that executable component, but is not a dedicated current-main
browser run or evidence that PR #53's documentation has merged. Real YouTube
playback and managed installation remain separate checks.

## G8: current PR/main execution demonstrated; enforcement remains open

The original [pilot PR #28](https://github.com/larsbx/school-ops/pull/28) is merged.
Current [workflow source](https://github.com/larsbx/school-ops/blob/09ba1b0a963413d057c2fcaa51861e151f565c74/.github/workflows/exercise-bank.yml)
declares unconditional PR, main-push, and merge-group triggers, the planner,
Python 3.11–3.13 validation, and an always-running final gate. The policy registers
19 suites. Actual recent execution is:

| Run, attempt 1 | Associated revision | Actual tested checkout | Result |
| --- | --- | --- | --- |
| [PR #69: 45973079244](https://github.com/larsbx/school-ops/actions/runs/45973079244) | Head `ac04819...`, base `2aa3eb3...` | `beb735751b4ef5c09726636f5cd86cc0df2e3aa9`, synthetic merge | Planner, all three Python jobs, and final gate passed |
| [Main push: 45973560922](https://github.com/larsbx/school-ops/actions/runs/45973560922) | `09ba1b0...` | `09ba1b0a963413d057c2fcaa51861e151f565c74` | Planner, all three Python jobs, and final gate passed |

Each planner passed 21 selector tests. Both selected full coverage after critical
policy/test changes. Each Python matrix job ran 277 repository tests with one
Windows-only registry integration skip, plus 22 passing archive tests. The final
gate logs explicitly report successful planning and matrix results. Full SHAs,
all ten job IDs, and the inspected checkout logs are indexed in the JSON record.

Both plan artifacts were downloaded and their archive digests matched GitHub's
metadata. However, `ci-plan.json` itself omits base/head/tested-source identities,
run/attempt IDs, and selector/policy digests. Its source attribution requires the
associated hosted metadata and logs; it is not a self-contained authenticated
source-bound receipt.

The [merge-group run query](https://api.github.com/repos/larsbx/school-ops/actions/runs?event=merge_group&per_page=100)
returned zero records. This is an observation of retained API results, not a
claim that the declared trigger has executed. The
[main branch metadata](https://api.github.com/repos/larsbx/school-ops/branches/main)
reports `protected: false`, and the
[ruleset query](https://api.github.com/repos/larsbx/school-ops/rulesets?includes_parents=true)
returned an empty list. The separate administrative protection-detail endpoint
returned **403, Resource not accessible by integration**. That inaccessible read
must not be relabeled as a 404 or complete administrative verification.

A job named `Exercise bank required gate` does not by itself establish protected
enforcement. Actual merge-group execution and a reviewed, verified required-check
decision remain open under G8 and
[SchoolOps issue #29](https://github.com/larsbx/school-ops/issues/29).

## Remaining obligations and next reproducible checks

| Obligation | Evidence needed for completion |
| --- | --- |
| Restore a usable native distribution | Build all intended OS/architectures from an explicitly selected current release revision; inspect Linux GUI/native results, packaged self-tests, source identity and hashes; retain a durable reviewed distribution and sign applications as appropriate |
| Production configuration and publication | Approve real portal hostnames, extension identity/key custody, version, update channel and hosting; perform the actual signing/Store or self-hosted publication and independently verify served bytes |
| Managed-device pilot | Reconcile the authoritative existing policy, install on the chosen managed platforms, and record ID/version, updates/restarts, standard-user enforcement, permitted real playback, denied/bypass cases, and removal behavior |
| Operator documentation and release record | Review open PR #53 and reconcile [issue #24](https://github.com/larsbx/school-ops/issues/24) with actual completed work and independently observed device evidence |
| Finish G8 | Demonstrate actual merge-group execution, review required contexts, and verify resulting enforcement; improve portable receipt identity if that acceptance contract is adopted |
| Estate adoption and inventory | Make any membership/v3 adoption decision separately, with a real manifest, declared boundaries and scoped formal evidence; this focused observation does not complete F2/G1 estate-wide coverage |

The inspected configuration still uses `approved-site.invalid`. Current repository
evidence does not establish approved school hostnames, a production extension
listing/hosting endpoint, enrolled devices, or applied production policy. The
earliest useful release check is therefore a fresh, retained native candidate
at a selected exact revision; production acceptance then requires the real
configuration and device evidence rather than inferring deployment from fixture
or formal success.
