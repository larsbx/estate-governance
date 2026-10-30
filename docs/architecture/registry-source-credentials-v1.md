# Registry source credential setup

This is the operator prerequisite for PR #16's private-source acceptance gate.
Adding the workflow does not create an App, install it, configure environment
protection, or prove hosted access. The P1 stays open until a real authenticated
run passes on the exact candidate revision. Domain authority, adoption decisions,
registry projection and `manifest-current-v1` are unchanged.

## Registration for the dedicated App

Use the personal `larsbx` account to
[open the prefilled registration](https://github.com/settings/apps/new?name=larsbx-estate-registry-reader&description=Read-only%20estate%20registry%20source%20acquisition&url=https%3A%2F%2Fgithub.com%2Flarsbx%2Festate-governance&public=false&webhook_active=false&contents=read).
This uses GitHub's documented registration URL parameters; it does not submit
the form, create an App, grant repository access or configure Actions secrets.
Review the form before submitting it:

| Setting | Value |
| --- | --- |
| App name | `larsbx-estate-registry-reader` (choose another unique name if unavailable) |
| Homepage | `https://github.com/larsbx/estate-governance` |
| Availability | Only this account (`public=false`) |
| Repository permission | Contents: Read-only; Metadata read is mandatory |
| Other repository/account permissions | No access |
| Webhooks | Inactive; no events or webhook secret |
| User authorization/OAuth | Not needed; no callback or setup URL |

After registration, install it on the exact source repositories described below,
record its App ID, and generate its private key in GitHub's App settings. Complete
the protected environment setup before storing that key. Keep the key inside
GitHub's environment-secret entry flow; do not paste it into chat or commit it.

The App registration, installation, key and protected environment are required
account-administration steps. A connected code-review integration does not
provide those capabilities or share a signed-in settings-browser session.

## Least-privilege installation

Create a dedicated GitHub App with **Contents: Read-only** and the mandatory
Metadata read permission. Disable webhooks; grant no write, Actions,
administration, checks, issues, organization, or account permissions. Install
it on **Only select repositories**, using every source member in the trusted
`policy/estate-registry.toml` except estate-governance itself (which is read from
the local full-history Git object store). The current scope is 20 repositories;
it includes these four private members:

- `larsbx/finite-julia-set-research`
- `larsbx/closure-fiber-of-multiplication-research`
- `larsbx/giant-fibers-finite-fields-thin-groups`
- `larsbx/oracles`

Public members are included so *every* remote fetch uses the same authenticated
path, with no anonymous fallback. The token request narrows both the repository
list and `permission-contents: read`; it never requests the owner's full
installation. The verifier independently checks `/installation/repositories`
against the exact trusted list and fails on missing, additional or inaccessible
repositories. A PAT is not an accepted substitute for this installation path.

Inspect the complete selection from the reviewed revision:

```sh
python -c 'import tomllib; d=tomllib.load(open("policy/estate-registry.toml", "rb")); print("\n".join(sorted(m["slug"] for m in d["member"] if m["id"] != "estate-governance")))'
```

## Protected credential release

Before adding a key, configure the **registry-source-read** environment in
estate-governance:

1. Require a trusted reviewer to approve each credentialled job. Enable
   **Prevent self-review** and disable administrator bypass of protection rules.
   Select a reviewer able to inspect this workflow and its pinned executable
   revision. Do not approve unreviewed same-repository PR workflows.
2. Store `REGISTRY_SOURCE_APP_ID` as an **environment variable** and
   `REGISTRY_SOURCE_APP_PRIVATE_KEY` as an **environment secret**. Do not put the
   private key in repository/organization secrets, workflow variables, PR text,
   Git configuration, or chat. Do not reuse a write-capable App.
3. Verify that a newly triggered run waits for environment approval before it
   can access the key. An environment auto-created by a workflow has **no
   protections**; its existence is not sufficient. Restrict environment refs
   further if useful, while retaining required reviewers for PR runs.
4. Approve only the exact reviewed run. Each new PR SHA must receive its own
   review; do not approve pending deployments in bulk. A workflow edit can
   request secrets through the environment, so review that workflow too, even
   though normal acquisition executes only the immutable tool pin.

The unprivileged test job has no environment or cross-repository secret. Fork
PR acquisition is refused before credential release and fails the final gate.
For a reviewed external contribution, bring the reviewed commit onto a trusted
same-repository PR and run the complete gate; never skip evidence for a fork.

The acquisition job checks out a full commit literal, imports the exact proposed
head as Git objects, and reads its registry as data. It does not execute its
Python, workflows, actions, hooks, submodules or tests. Preparation runs before
token creation. The token reaches only the trusted verification step. The pinned
App-token action revokes it in its post step (including verification failure);
`skip-token-revoke` must remain false. Do not pass the token between jobs.

## Hosted acceptance and repair

After configuring the App/environment, rerun CI on the exact current PR head.
Preserve the run URL, proposed head SHA, tested revision in the receipt,
acquisition job result, final `Registry snapshot freshness` result, and uploaded
`registry-source-observation` receipt. Acceptance requires all 21 members,
`complete = true`, the expected authentication scope, and `validation.passed =
true`, plus the existing test/audit job. Never upload captured Git repositories:
they contain private manifests/workflows and ancestry.

Classify failures before changing code:

| Failure | Required response |
| --- | --- |
| Missing App ID/key or waiting for reviewer | Complete/approve the protected configuration; no authenticated result exists yet. |
| Token minting or scope HTTP 401/403/404 | Repair App key, installation selection or Contents read access; no anonymous retry. |
| Git fetch fails | Check source availability/access and immutable revisions; incomplete receipt remains a failure. |
| Source revision or receipt mismatch | Reacquire exact evidence; preserve the provenance checks. |
| Current manifest/projection drift | Regenerate and review registry/adopter changes under the existing governance process. |
| Hosted success with full receipt | Record exact evidence, then resolve the P1 and integrate only if the other gates pass. |

The stable `Registry snapshot freshness` job runs even when acquisition is
skipped, cancelled or fails, and returns failure for any non-success dependency.
The workflow does not configure branch protection: the operator must require
`test` and `Registry snapshot freshness`. Existing write-authority limitations
remain; no server-side enforcement beyond configured GitHub protections is
claimed.

Updating acquisition code or membership requires a new immutable reviewed tool
commit and a separate update to the workflow's checkout pin. Review the tool
commit before approving its first credentialled run. Do not replace the pin
with the candidate SHA, a branch, an expression from PR data, or `HEAD`.

References: [GitHub App token action](https://github.com/actions/create-github-app-token),
[registration URL parameters](https://docs.github.com/en/apps/sharing-github-apps/registering-a-github-app-using-url-parameters),
[installation-token repository access](https://docs.github.com/en/rest/apps/installations#list-repositories-accessible-to-the-app-installation),
[environment secrets and required reviewers](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).
