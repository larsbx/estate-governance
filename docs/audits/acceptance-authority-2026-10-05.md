# Repository acceptance authority audit — 2026-10-05

PR #5 was merged at `fcee6e05c7f74ab2fb4b27183a6c7c3db018c07e` before
this reconciliation. Its unconditional canonical-acceptance rule rejects Julia
Oracle Lab's explicit zero-authority model. This audit covers the seven entries
in the v2 contract's Adopters register, including governance itself.

## Authority interpretation

The v2 rule quantifies over acceptance/effect boundaries that a repository owns;
it does not require every repository to own one. Canonical code ownership is
independent of acceptance authority. Julia Oracle Lab's registry/binding kernel
is canonical, but its
[authority-boundary document](https://github.com/larsbx/julia-oracle-lab/blob/4eac858ef90da435df620c413ec88df4ebb0c6a5/docs/AUTHORITY_BOUNDARY.md)
places every trusted acceptance boundary outside the lab and forbids acceptance,
proof, authorization and deployment verdicts. Its existing manifest declares
`acceptance_authority = false`; no consumer authority is migrated here.

The corrected audit requires exactly one canonical language with the kernel role
and an explicit Boolean acceptance declaration. `true` gives one acceptance
language; `false` gives zero and declares no owned acceptance/effect boundary.
Missing or non-Boolean canonical declarations fail closed. Supporting languages
remain unable to accept under either model, and their supplied declarations must
also be Boolean. The contract and manifest template now describe both models,
including the repository-wide scope of the multi-program extension.

## Commit-bound adopter checks

For each recorded snapshot, the existing manifest's language declarations were
checked directly with `validate_languages`. The complete `validate` call also
passed with only the governance audit digest replaced in a deep copy of the
parsed manifest to simulate adoption of the new audit. The stored manifest,
consumer checkout, vendored pins and authority declarations were unchanged.
These are prospective compatibility checks, not claims that consumers have
re-pinned or that their own CI gates ran.

| Repository | Source commit | Canonical language | Acceptance authority | #5 rule | Corrected rule / full prospective audit |
| --- | --- | --- | --- | --- | --- |
| `larsbx/finite-math-kernels` | `bf3f95c9cab794e263e01a71ca7ec41f08bb311f` | Mojo | `true` | passes | passes / passes |
| `larsbx/finite-mandelbrot-research` | `11b6f0474c31b81f206a1fcf3c630f1bd9fbe9ff` | Mojo | `true` | passes | passes / passes |
| `larsbx/finite-julia-set-research` | `04db96236fd5c583414905b7014f05a4f9b00a75` | Mojo | `true` | passes | passes / passes |
| `larsbx/julia-oracle-lab` | `4eac858ef90da435df620c413ec88df4ebb0c6a5` | Julia | `false` | rejects | passes / passes |
| `larsbx/langlands-lab` | `88f3fb692b7fcf8b0785378317e79a5dd3d15178` | Python | `true` | passes | passes / passes |
| `larsbx/mandelbrot-bulbs-and-ford-circles-research` | `eed8f3a54e5f6122522a8c8c47ebd8b212c1440d` | Python | `true` | passes | passes / passes |
| `larsbx/estate-governance` | `fcee6e05c7f74ab2fb4b27183a6c7c3db018c07e` | Python | `true` | passes | passes / passes |

The governance row uses the recorded base manifest and tree with this patch's
working audit. Five public consumer snapshots came from shallow Git checkouts.
Finite Julia Set Research's 152 tracked blobs were read at its exact commit
through the connected GitHub API and independently checked against their Git
blob SHA-1s before constructing the tree. Every registered adopter was read;
none was excluded for access reasons.

The machine-readable [snapshot receipt](acceptance-authority-2026-10-05.json)
records source commits, manifest SHA-256s, all language declarations, and outcomes.
The audited implementation's SHA-256 is
`412a64dea58d709aae21e5a0315b8e7e96488c310a9d999267927ba3d8146a30`.

## Reproduction and regressions

Place each recorded consumer snapshot beneath `adopters/<repository-name>` and
use the corrected governance checkout. Its contract register determines coverage.
This reproduces the rule and full prospective checks without changing consumer
files:

```python
import copy
import re
from pathlib import Path
import sys

# Run from the governance checkout, beside ../adopters/<repository-name>.
root = Path.cwd()
sys.path.insert(0, str(root / "kernel"))
import audit_estate_layout as audit

contract = (root / audit.CONTRACT).read_text(encoding="utf-8")
adopters = re.findall(r"^\| `(larsbx/[^`]+)` \|", contract, flags=re.M)
assert adopters
for slug in adopters:
    name = slug.split("/")[1]
    consumer = root if slug == audit.GOVERNANCE_REPOSITORY else root.parent / "adopters" / name
    data = audit.load(consumer / audit.MANIFEST)
    assert data["repo"]["slug"] == slug
    audit.validate_languages(data)
    prospective = copy.deepcopy(data)
    for dep in prospective.get("dep", []):
        if dep["id"] == audit.GOVERNANCE_ID:
            dep["pin"] = "sha256:" + audit.sha256(Path(audit.__file__))
    audit.validate(prospective, consumer)
    print(slug, "authority and full prospective audit passed")
```

Validation on this patch: `python -m pytest` reports 112 passing tests;
`python kernel/audit_estate_layout.py` passes; `git diff --check` passes.
Regression coverage includes the Julia-style zero-authority kernel under both
transitional and canonical layouts, omission, malformed flags on either language
role, supporting-language escalation under both models, and multiple canonical
languages under every Boolean combination. The pre-reconciliation audit rejects
the recorded Julia manifest with `canonical language must hold acceptance authority`.

The audit validates declarations and layout, not arbitrary source-code verdict
behavior. Existing pins keep using their old audit until an explicit pin bump.
Consumer CI and any configured Forgejo/Woodpecker source/merge authority remain
outside this governance-only correction.
