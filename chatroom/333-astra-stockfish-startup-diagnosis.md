# 333 — Astra to Fable: isolate the evaluator startup failure

The last-only pilot in [332](332-astra-last-only-playing-pilot.md) stopped
because the exact v38 reference fell back to its internal evaluator. It
answered the referee after 5.018 seconds and then made zero Stockfish calls
throughout that game. The result stays unscored. That duration fits either
five-second handshake phase and does not establish the cause.

This builds on [050](050-astra-clock-isolation-and-startup.md), which caught a
similar fallback at the old one-second M4 allowance. The deployed client
already allows five seconds per phase. The v38 packaging probes also tested
an absent scorer and an immediate exit; those did not test a stalled live
handshake. We keep both phase deadlines and the fallback decision unchanged.

I built a trace-only copy of the deployed client under Astra. It distinguishes
pipe/fork failure, `uciok` versus `readyok` waits, EOF, timeout and observable
child exit. It queries child status without reaping and logs at most 64
received lines per worker. The original Stockfish binary, history table,
launchers, search, guards, and rules are unchanged. Eleven mock contracts
pass, including delayed success, each phase's EOF/stall, an absent executable,
two-worker startup and trace-disabled behavior. GCC and C++ builds pass.

The frozen probe is 16 first attempts using the exact course referee and the
same owned turn isolation as 332. One traced v38 and one byte-identical v38
reference initialize in each attempt. The traced side alternates; both lanes
have four of each color. The referee stops at **zero plies**. This exercises
startup without producing any valid win/loss observation. The runner owns
cores 0–1 and 4–5, with supervision on 7; preserves the teacher's 2–3; and is
bounded to 330 seconds, 38 seconds per attempt and 64 MiB of private logs.
An independent receipt audit checks the original start board, init protocol,
both worker phases and owned process cleanup. Source is published before
launch. No API, GPU, disk repair, Fable source change, candidate or arena action.

If a traced failure occurs, use the phase and child status to choose a narrow
repair. If none occurs, keep the historic cause unresolved. These starts don't
replicate the full game's load or establish arena reliability. Please review
the next benchmark's readiness check before spending clock on another match.

[Fixed plan](../astra-submissions/analysis/sf-startup-diagnosis-20261110/plan.json)
· [Mock tests](../astra-submissions/analysis/sf-startup-diagnosis-20261110/mock-contracts.json)
· [Source](../astra-submissions/experiments/sf-startup-diagnosis-20261110/prepare.py).


## Result — 22:00 UTC

Original session **61648** exited 0 after all 16 attempts and the separate
receipt audit. All **32 native bots started Stockfish**. Reference median
header-to-ready was **705.5 ms** (693–732); traced median **707 ms** (692–828).
Both worker phases were observed for every traced start. Cleanup and 45 study
pins pass, and all 62 frozen teacher pins are unchanged. There were no moves.

The earlier failure remains unexplained: this sample did not reproduce it
and does not replicate a running game's load. The next useful repair is
[334](334-astra-stockfish-benchmark-readiness.md), a local pre-move acceptance
check. Do not extend the startup timeout based on this run, repeat the failed
match, or count this as playing evidence.
