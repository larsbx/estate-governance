// An abstract evidence lifecycle, not a model of GitHub or the Python auditor.
// Exact integer identity equality stands for source and policy identity checks.
// Recorded tool outcomes are inputs; their authenticity is outside this model.
module EstateFormal {
  type Evidence = { source: int, policy: int, result: str }
  type State = {
    source: int, policy: int, lean: Evidence, quint: Evidence,
    verified: bool, domainAuthority: bool,
  }

  pure def evidence(source: int, policy: int, result: str): Evidence =
    { source: source, policy: policy, result: result }
  pure def current(state: State, observation: Evidence): bool =
    observation.result == "passed" and observation.source == state.source and observation.policy == state.policy
  pure def ready(state: State): bool = current(state, state.lean) and current(state, state.quint)

  var s: State

  action init = s' = {
    source: 0, policy: 0,
    lean: evidence(0, 0, "missing"), quint: evidence(0, 0, "missing"),
    verified: false, domainAuthority: false,
  }
  action recordLean(observation: Evidence): bool = s' = { ...s, lean: observation, verified: false }
  action recordQuint(observation: Evidence): bool = s' = { ...s, quint: observation, verified: false }
  action reviseSource = all { s.source < 2, s' = { ...s, source: s.source + 1, verified: false } }
  action revisePolicy = all { s.policy < 2, s' = { ...s, policy: s.policy + 1, verified: false } }
  action verify = all { ready(s), s' = { ...s, verified: true } }
  action idle = s' = s

  action step = any {
    recordLean(evidence(s.source, s.policy, "passed")),
    recordQuint(evidence(s.source, s.policy, "passed")),
    recordLean(evidence(s.source, s.policy, "queued")),
    recordQuint(evidence(s.source, s.policy, "running")),
    recordLean(evidence(s.source, s.policy, "failed")),
    recordQuint(evidence(s.source, s.policy, "failed")),
    recordLean(evidence(0, 0, "passed")),
    recordQuint(evidence(0, 0, "passed")),
    reviseSource, revisePolicy, verify, idle,
  }

  val safety = (s.verified implies ready(s)) and not(s.domainAuthority)
  val verifiedWitness = s.verified

  run missingEvidenceTest = init.expect(not(ready(s)) and not(s.verified) and safety)
  run bothChecksTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).expect(s.verified and ready(s) and safety)
  run singleLaneTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .expect(not(ready(s)) and not(s.verified) and safety)
  run staleSourceTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).then(reviseSource)
    .then(recordQuint(evidence(1, 0, "passed")))
    .expect(not(ready(s)) and not(s.verified) and safety)
  run stalePolicyTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).then(revisePolicy)
    .then(recordLean(evidence(0, 1, "passed")))
    .expect(not(ready(s)) and not(s.verified) and safety)
  run failedResultTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).then(recordQuint(evidence(0, 0, "failed")))
    .expect(not(ready(s)) and not(s.verified) and safety)
  run queuedResultTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).then(recordLean(evidence(0, 0, "queued")))
    .expect(not(ready(s)) and not(s.verified) and safety)
  run authorityPreservedTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).expect(s.verified and not(s.domainAuthority) and safety)
  run recoveryRequiresBothFreshResultsTest = init
    .then(recordLean(evidence(0, 0, "passed")))
    .then(recordQuint(evidence(0, 0, "passed")))
    .then(verify).then(reviseSource).then(revisePolicy)
    .then(recordLean(evidence(1, 1, "passed")))
    .then(recordQuint(evidence(1, 1, "passed")))
    .then(verify).expect(s.verified and safety)

  // Deliberately incorrect verification transition. The gate separately runs
  // this deterministic step and requires an actual safety counterexample.
  action unsafeStep = s' = { ...s, verified: true }
}
