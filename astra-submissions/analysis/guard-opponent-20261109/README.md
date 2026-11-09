# Matched Misty panel: frozen after the guard pilot passed

The guard candidate scored 10.5/16 against exact v38 with no technical fault.
Its independent referee audit passes. This freezes 32 further games: 16 per
arm against the same installed Misty 0.1.3, v1.6 profile. The opponent uses
the repaired course-action adapter, with Rust required. This is Brian Liou's
local implementation, not Brian Hu Zhang's original Obscuro or verified
current arena bytes.

Eight seed blocks each contain both colors and both arms. Identical engine
and opponent seeds are used within matched cells; first arm alternates.
Blocks stay on the same core pair. Three lanes use 0–1, 2–3 and 4–5. At 180+2,
each first-attempt game has a 2,450-second bound and the batch a four-hour
bound; a lane starts a game only when a full game bound remains. Any technical
fault, unverified cleanup, adapter fallback or capture warning stops all new
games. In-flight legal games may finish. No started attempt is replaced.

The gate requires all 32 clean games, at least eight candidate points and
at least two more candidate points than the 16-game v38 control. Passing
earns candidate review, not a claim of Elo gain or automatic upload. A
technical stop leaves the comparison inconclusive and explicit missing cells.
Seeds do not guarantee identical wall-clock search or every Misty choice.

Off-turn process groups are frozen using the audited course hook; buffered
observations are charged on the next active turn. That is scheduling control,
not a security sandbox. Each game runs in a separate worker process, records
owned process identities, checks its full replay against the native rules,
and freezes output hashes after cleanup. A separate course-referee audit
will be applied to the completed panel.

All 198 dependencies are pinned: playing native binaries and sources,
Stockfish and history, Python/Rust Misty package files, adapter, course
observation tracker, referee and control hook. Six real protocol probes pass
across all three engines and both colors, with legal moves and no live owned
children. A constructor-argument mistake was caught before any match; the
preflight-only plan and correction are retained. Playing bytes, queue and
thresholds were unchanged. The final plan/source will be pushed before launch.
No GPU work, ingestion, model fit or arena change is part of this panel.
