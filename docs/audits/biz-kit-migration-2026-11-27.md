# Biz-kit migration and dependency status — November 27, 2026

Source baseline [Biz-kit cef73dceb75b863a90ad21aa2c2c70f813ea0d3e](https://github.com/larsbx/biz-kit/commit/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e).
Estate baseline b851c92fceb88c8e6f4604664cf975b567ade161.

## Current disposition

| Area | Verified source or GitHub state | Remaining acceptance |
| --- | --- | --- |
| Eatsbot legacy source | [PR #426](https://github.com/larsbx/biz-kit/pull/426) merged as bc53e414f577b0113f8f844285f8cfb9e2cfcee5. Current main has removed the legacy Eatsbot apps and Kafka extension. The restaurant release uses the replacement host. | Observe the running replacement revision and health, then retain the standalone infrastructure and credential retirement records. |
| Disposable Eatsbot stack | The owner-confirmed November 16 inventory records no customer data, unused Kafka and no job queue on adder-ws. The approved switch starts an empty replacement ledger. | Apply that disposition only to the inventoried disposable stack. Inventory obligations and data in any other copy. |
| SpruceGoose rehosting | Web/native authentication lives in task_host, and the session store lives in biz_kit_identity. Native session rows are retained. SpruceGoose still exists on main. | Native sign-in, revocation and portal integration at the deployed host, artifact custody, project owner coverage and explained parity. |
| Archive and writer fence | [#443](https://github.com/larsbx/biz-kit/pull/443) and [#441](https://github.com/larsbx/biz-kit/pull/441) merged. #441 merge is cc51872668483161d2287dc07c91bf215a374ce2. Strict archive preflight and fence safeguards are implemented. | Source quiescence, final durable archive, outbox disposition, production fence/replay and Mama succession receipts. |
| Dependency PR #390 | [Closed without merge](https://github.com/larsbx/biz-kit/pull/390), head 5cb159f2a4a57afcd87e24332bb59346fa9f4966. Current main locks AshAuthentication rc.17 and has no KafkaEx lock entry. | Attribute present compatibility to current source and its checks. Closure of #390 supplies no acceptance verdict. |
| Dependency PR #453 | [Open](https://github.com/larsbx/biz-kit/pull/453), head 78c22f59458b3adc7ef2ff7526c7ae2ded4dae7a. This is a newer dependency review surface. | Review its own failures against its base and verify the Finch/TLS test repair at the eventual patched revision. |

## Source records

- [Eatsbot decommission checklist](https://github.com/larsbx/biz-kit/blob/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e/docs/architecture/2026-11-07-eatsbot-decommission.md) records completed source removal and outstanding host, Fly and credential evidence.
- [SpruceGoose decommission checklist](https://github.com/larsbx/biz-kit/blob/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e/docs/architecture/2026-11-06-sprucegoose-decommission.md) records rehosting, retained writers and remaining operational gates.
- [Task host migration](https://github.com/larsbx/biz-kit/blob/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e/docs/architecture/2026-11-09-task-host.md) records authentication ownership and native-session preservation.
- [Retirement remediation validation](https://github.com/larsbx/biz-kit/blob/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e/docs/architecture/2026-11-23-retirement-remediation-validation.md) reports strict umbrella compilation and 64 local acceptance tests at 8b14a9b03c20ebb21063f9224cabf574527c41fa. Those results belong to that revision.
- [Cutover acceptance runbook](https://github.com/larsbx/biz-kit/blob/cef73dceb75b863a90ad21aa2c2c70f813ea0d3e/docs/architecture/2026-11-23-retirement-cutover-acceptance.md) defines the operational receipts still needed.

## Observed dependency checks

GitHub's workflow listing for #453's exact head returned 34 runs at inspection.

| Workflow | Observed result | Evidence |
| --- | --- | --- |
| Operations workspace acceptance | Success | [45957425873](https://github.com/larsbx/biz-kit/actions/runs/45957425873) |
| Portal authentication acceptance | Failure | [45957425976](https://github.com/larsbx/biz-kit/actions/runs/45957425976) |
| Consolidation | Failure | [45957425566](https://github.com/larsbx/biz-kit/actions/runs/45957425566) |

This reconciliation inspected source, PR metadata and workflow outcomes. It did
not execute application tests or classify the individual #453 failures. The
Finch repair is tracked in its separate task. Next acceptance is a comparison
of the repaired candidate and its base using production TLS/hostname checks,
permitted loopback HTTP, portal/native-session tests and Consolidation.

## Earlier review superseded

The November 13 review of #390 concerned legacy Eatsbot magic-link and Kafka
code that has since been removed. Its isolated Kafka comparison and regression
patch remain historical evidence for that source. Current restaurant
acceptance follows the replacement host and Dispatch path.

That review reproduced an orchestration release fixture missing task_host's
SECRET_KEY_BASE on both old revisions. A temporary fixture correction passed
13 tests then. That result does not describe the current Consolidation failure.

This audit records source and evidence ownership. Production retirement,
dependency approval, deployment and merge decisions remain with the owner.
