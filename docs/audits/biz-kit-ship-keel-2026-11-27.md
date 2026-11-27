# Biz-kit, Keel, Graft and Ship integration status

Observed 2026-11-27 through authenticated GitHub repository reads.
Scope is the integration developed in this conversation. This is a dated
implementation assessment for estate roadmap obligations F2, F5 and G9.

## Current sources

| Repository | Inspected main revision | Observation |
| --- | --- | --- |
| larsbx/biz-kit | cef73dceb75b863a90ad21aa2c2c70f813ea0d3e | Complete recursive tree lacks apps/keel/lib/keel/release_review.ex. Operations configuration lacks release_review_url. |
| larsbx/ship | cc32c118b78fa68050360c643631b303d9be6465 | Complete recursive tree lacks control/bizkit_review.py. |
| larsbx/dev-ops | e8f0601d6751383c7418af7a1dec390880636b92 | PR #23 reports merged destination integrity verification. Live staging acceptance was outside this assessment. |

The current branches remain at these exact revisions:

| Branch | Revision | Recorded behavior |
| --- | --- | --- |
| biz-kit feature/operations-release-review | fc3b1dbc74741989aacec7f65d322273ceefd6ae | Scoped Operations link, Keel decision signer, request and evidence binding, independent OpenSSL signature test |
| ship feature/biz-kit-release-review | 173d88315647cce3ccb0a3c8bf6f45ba86c2be29 | Signed manifest/Graft/Keel review page and pinned Ed25519 signature verifier |

The absence of these paths in current main establishes an adoption gap.
It does not establish whether other changes superseded the proposed design.
Reconcile current host and governance interfaces before integration.

## Evidence

[Biz-kit Keel contract run 43331363586](https://github.com/larsbx/biz-kit/actions/runs/43331363586)
completed successfully for fc3b1dbc74741989aacec7f65d322273ceefd6ae.
The workflow compiles Keel and executes release-review signature tests.
This supersedes the earlier queued observation. The preceding run
43301193029 failed because a test helper conflicted with Kernel.binding/0;
the replacement renames the helper and checks the actual producer output
with OpenSSL.

The successful run is scoped to the Keel contract. Operations browser
acceptance, current-main compatibility, authenticated ledger admission,
and automatic delivery to Ship remain unverified by that run.
No new tests were executed for this documentation update.

[Ship PR #5](https://github.com/larsbx/ship/pull/5) reports merged approval/change
forms. [Dev-ops PR #23](https://github.com/larsbx/dev-ops/pull/23) reports merged
destination integrity verification. These merges do not establish adoption
of the separate Biz-kit/Ship integration branches.

## Integration ownership and obligations

Biz-kit owns the user workflow, authenticated governance state, Keel inputs
and admitted decisions. Graft supplies source integrity evidence. Ship
provides source review and the deployment request executor.

| ID | Remaining obligation | Reproducible acceptance |
| --- | --- | --- |
| BKS1 | Reconcile both integration branches with current main | Exact-source builds, Operations scope tests and Ship backend/browser suites pass on the reconciled revisions |
| BKS2 | Derive signer inputs from admitted Biz-kit governance state | Forged body, ballots, proposal, stale policy and revoked principal fail before signing; replay reconstructs the same binding |
| BKS3 | Deliver signed decisions automatically | Retry, duplicate delivery, restart and conflicting record tests preserve one admitted meaning and the exact request/evidence association |
| BKS4 | Validate current authority when acting on a decision | Policy/key revocation, expired authority, changed target generation and substituted action/release/evidence are refused at the declared enforcement point |
| BKS5 | Complete the Biz-kit user flow | An authenticated user reviews source, records a scoped decision and follows execution status; unauthorized users receive no scoped metadata |
| BKS6 | Formalize the integration under estate v3 | Lean obligations, Quint state model, implementation correspondence scope, pinned tools and source-bound execution receipts cover the named authority and replay boundaries |

Keel's signature attests the supplied inputs and outcome. The producer
currently accepts caller-supplied organization and votes. Authenticated
governance admission and a public-key signature are distinct obligations.
The historical decision display grants no deployment permission.

## Next acceptance milestone

Reconcile BKS1, then implement BKS2 and BKS3 as one isolated replay:
admit a proposal and ballots through Biz-kit, compute the Keel result from
that admitted state, sign its exact request and Graft binding, retry delivery,
and verify it in Ship. Include negative controls for revoked authority,
substituted evidence and a changed target generation. Record the exact
Biz-kit and Ship revisions with backend, browser, Lean and Quint results.

## Source links

- [Biz-kit branch](https://github.com/larsbx/biz-kit/tree/fc3b1dbc74741989aacec7f65d322273ceefd6ae)
- [Ship branch](https://github.com/larsbx/ship/tree/173d88315647cce3ccb0a3c8bf6f45ba86c2be29)
- [Biz-kit inspected main](https://github.com/larsbx/biz-kit/tree/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e)
- [Ship inspected main](https://github.com/larsbx/ship/tree/cc32c118b78fa68050360c643631b303d9be6465)
