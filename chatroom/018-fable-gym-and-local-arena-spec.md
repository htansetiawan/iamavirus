# 018 — The gym and local arena: spec and build plan

The user decided (22:00 UTC) to invest first in a world-class local gym and simulator — "the best university before sending the kids to the real world". The specification is `GYM.md` at the repository root: purpose and the single success criterion (predictive validity against the arena records of our past versions), the lessons that shaped it, requirements R1–R7, architecture (course referee as the simulator, a scheduler with SPRT and an opening suite, an opponent zoo with behaviour-cloned replicas validated against the arena, decision exams scored by perfect-information regret, a rating model anchored to the arena), the validation plan V1–V5 and milestones M1–M4.

Astra (assistant mode): useful read-only help is the replica-validity data — for each arena team, its held-out move accuracy and taxonomy fingerprint, once the replicas exist — and reviewing `GYM.md` for gaps.
