import Init

/-!
An abstract model of the estate's two required formal-evidence lanes.

Natural-number identities stand for opaque, exactly compared source and policy
identities; this model does not implement hashing or authenticate subprocess
results. A recorded result is an input to the model. Python correspondence and
the accuracy of that input are separate obligations.
-/
namespace EstateFormal

inductive Result where
  | missing | queued | running | passed | failed
  deriving DecidableEq, Repr

structure Evidence where
  source : Nat
  policy : Nat
  result : Result
  deriving DecidableEq, Repr

structure State where
  source : Nat
  policy : Nat
  lean : Evidence
  quint : Evidence
  verified : Bool
  domainAuthority : Bool
  deriving DecidableEq, Repr

def initial (authority : Bool) (source policy : Nat) : State :=
  { source, policy,
    lean := { source, policy, result := .missing },
    quint := { source, policy, result := .missing },
    verified := false, domainAuthority := authority }

def Current (s : State) (e : Evidence) : Prop :=
  e.result = .passed ∧ e.source = s.source ∧ e.policy = s.policy

def Ready (s : State) : Prop := Current s s.lean ∧ Current s s.quint

def VerifiedSafe (s : State) : Prop := s.verified = true → Ready s

def recordLean (s : State) (e : Evidence) : State :=
  { s with lean := e, verified := false }

def recordQuint (s : State) (e : Evidence) : State :=
  { s with quint := e, verified := false }

def reviseSource (s : State) (source : Nat) : State :=
  { s with source, verified := false }

def revisePolicy (s : State) (policy : Nat) : State :=
  { s with policy, verified := false }

def markVerified (s : State) : State := { s with verified := true }

inductive Transition : State → State → Prop where
  | leanResult (s : State) (e : Evidence) : Transition s (recordLean s e)
  | quintResult (s : State) (e : Evidence) : Transition s (recordQuint s e)
  | sourceChange (s : State) (source : Nat) : Transition s (reviseSource s source)
  | policyChange (s : State) (policy : Nat) : Transition s (revisePolicy s policy)
  | verify (s : State) (ready : Ready s) : Transition s (markVerified s)
  | idle (s : State) : Transition s s

inductive Reachable (authority : Bool) (source policy : Nat) : State → Prop where
  | start : Reachable authority source policy (initial authority source policy)
  | next {s t : State} : Reachable authority source policy s → Transition s t →
      Reachable authority source policy t

theorem ready_requires_both (s : State) (h : Ready s) :
    s.lean.result = .passed ∧ s.quint.result = .passed :=
  ⟨h.1.1, h.2.1⟩

theorem ready_requires_same_source (s : State) (h : Ready s) :
    s.lean.source = s.source ∧ s.quint.source = s.source :=
  ⟨h.1.2.1, h.2.2.1⟩

theorem ready_requires_same_policy (s : State) (h : Ready s) :
    s.lean.policy = s.policy ∧ s.quint.policy = s.policy :=
  ⟨h.1.2.2, h.2.2.2⟩

theorem nonpassed_lean_not_ready (s : State) (h : s.lean.result ≠ .passed) :
    ¬ Ready s := fun ready => h ready.1.1

theorem nonpassed_quint_not_ready (s : State) (h : s.quint.result ≠ .passed) :
    ¬ Ready s := fun ready => h ready.2.1

theorem stale_lean_source_not_ready (s : State) (h : s.lean.source ≠ s.source) :
    ¬ Ready s := fun ready => h ready.1.2.1

theorem stale_quint_policy_not_ready (s : State) (h : s.quint.policy ≠ s.policy) :
    ¬ Ready s := fun ready => h ready.2.2.2

theorem revise_source_invalidates (s : State) (source : Nat) :
    (reviseSource s source).verified = false := rfl

theorem revise_policy_invalidates (s : State) (policy : Nat) :
    (revisePolicy s policy).verified = false := rfl

theorem record_lean_invalidates (s : State) (e : Evidence) :
    (recordLean s e).verified = false := rfl

theorem record_quint_invalidates (s : State) (e : Evidence) :
    (recordQuint s e).verified = false := rfl

theorem initial_safe (authority : Bool) (source policy : Nat) :
    VerifiedSafe (initial authority source policy) := by
  intro h
  cases h

theorem transition_preserves_verified {s t : State}
    (hstep : Transition s t) (hsafe : VerifiedSafe s) : VerifiedSafe t := by
  cases hstep with
  | leanResult e =>
    intro h
    cases h
  | quintResult e =>
    intro h
    cases h
  | sourceChange source =>
    intro h
    cases h
  | policyChange policy =>
    intro h
    cases h
  | verify ready =>
    intro _
    exact ready
  | idle => exact hsafe

theorem reachable_verified_requires_both {authority : Bool} {source policy : Nat}
    {s : State} (h : Reachable authority source policy s) :
    s.verified = true →
      Current s s.lean ∧ Current s s.quint := by
  induction h with
  | start => exact initial_safe authority source policy
  | next _ step ih => exact transition_preserves_verified step ih

theorem transition_preserves_authority {s t : State} (h : Transition s t) :
    t.domainAuthority = s.domainAuthority := by
  cases h <;> rfl

theorem reachable_preserves_authority {authority : Bool} {source policy : Nat}
    {s : State} (h : Reachable authority source policy s) :
    s.domainAuthority = authority := by
  induction h with
  | start => rfl
  | next _ step ih => exact (transition_preserves_authority step).trans ih

/-- A concrete successful evidence state still has no domain authority. -/
theorem verification_does_not_grant_authority :
    ∃ s : State, Ready s ∧ s.verified = true ∧ s.domainAuthority = false := by
  let e : Evidence := { source := 0, policy := 0, result := .passed }
  exact ⟨{ source := 0, policy := 0, lean := e, quint := e,
           verified := true, domainAuthority := false },
         ⟨⟨rfl, rfl, rfl⟩, ⟨rfl, rfl, rfl⟩⟩, rfl, rfl⟩

end EstateFormal
