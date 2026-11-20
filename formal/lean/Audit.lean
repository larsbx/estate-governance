import Lean.Elab.Command
import Lean.Util.CollectAxioms
import EstateFormal

open Lean Elab Command

/- Every local declaration is audited transitively. Required obligations must
exist as theorems. No application-supplied axiom or `sorryAx` is allowed. -/
elab "audit_estate_formal" : command => do
  let env ← getEnv
  let required : Array Name := #[
    ``EstateFormal.ready_requires_both,
    ``EstateFormal.ready_requires_same_source,
    ``EstateFormal.ready_requires_same_policy,
    ``EstateFormal.nonpassed_lean_not_ready,
    ``EstateFormal.nonpassed_quint_not_ready,
    ``EstateFormal.stale_lean_source_not_ready,
    ``EstateFormal.stale_quint_policy_not_ready,
    ``EstateFormal.revise_source_invalidates,
    ``EstateFormal.revise_policy_invalidates,
    ``EstateFormal.record_lean_invalidates,
    ``EstateFormal.record_quint_invalidates,
    ``EstateFormal.initial_safe,
    ``EstateFormal.transition_preserves_verified,
    ``EstateFormal.reachable_verified_requires_both,
    ``EstateFormal.transition_preserves_authority,
    ``EstateFormal.reachable_preserves_authority,
    ``EstateFormal.verification_does_not_grant_authority]
  for name in required do
    match env.find? name with
    | none => throwError "missing formal obligation: {name}"
    | some info =>
      unless info.isTheorem do
        throwError "formal obligation is not a theorem: {name}"
      let axioms ← collectAxioms name
      unless axioms.isEmpty do
        throwError "required formal theorem depends on axioms: {name}: {axioms}"
  -- Lean generates structure injectivity support using propext. The declared
  -- obligations above remain axiom-free; no other support axiom is permitted.
  let allowed : Array Name := #[``propext]
  let mut used : Array Name := #[]
  let mut declarations : Nat := 0
  let mut theorems : Nat := 0
  for (name, info) in env.constants.toList do
    if (`EstateFormal).isPrefixOf name then
      declarations := declarations + 1
      if info.isTheorem then theorems := theorems + 1
      let axioms ← collectAxioms name
      for axiomName in axioms do
        if !used.contains axiomName then used := used.push axiomName
        unless allowed.contains axiomName do
          throwError "formal axiom audit rejected {name}: {axiomName}"
  logInfo m!"Estate formal axiom audit passed: {required.size} required theorems without axioms; {declarations} declarations; {theorems} theorem declarations; support axioms: {used}"

audit_estate_formal
