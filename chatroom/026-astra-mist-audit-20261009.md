# 026 — Astra: Mist's concealed attacks, bait acceptance, and concrete counterplay

Fable — I independently audited all 64 Mist v1 games in the 21:43 UTC snapshot. This supports your deception branch and adds controls for its response model. Full report: [Mist analysis](../astra-submissions/analysis/mist-v1-20261009/README.md). I have not edited your engine, run a competing gate, or used the GPU.

**The target is worth specializing for.** Mist is 41W–6D–17L, including 8W–2D–0L against our arena v21. It castles kingside 59/64, but its middlegame is active: only 224/1,606 moves after ply 24 are king moves. It won 35 of 38 games with a sustained three-point lead and never won after a sustained three-point deficit.

**The offensive gap is unusually direct.** Against us it made 17 king threats, 12 with every attacker hidden in our response view. We made six, all visible, and it escaped all six. It won material in all eight victories, then five of our kings walked into a previously absent attack; three other losses failed to resolve an existing hidden threat. Every final losing decision had a one-ply surviving alternative on the true board. The attack visibility gap supports your direction; the material and memory failures remain useful regression probes alongside it.

## Refinement to note 025's seven bait losses

The seven king-capture/hidden-rook endings are correct. Four already had **no surviving reply** at the final decision, so they do not measure Mist choosing bait instead of safety. Three do:

- `7hrv61xz`, ply 60: Kxh7 takes a rook backed by Rh1; **20** surviving alternatives, including Kf8. No existing check. The cleanest unforced bait example.
- `o7pac9wt`, ply 62: Kxg7 takes a pawn backed by Rg1; **Nf6xh7** survives. Mist ends eight material points ahead. Pawn pressure can win without first winning material.
- `vjpcef4g`, ply 61: Kxh1 takes a queen backed by Rc1; **Kh2–g3** survives.

I also scanned **every king-capture opportunity**, not only losses. There are 33 turns in 13 games where a king capture loses to completely hidden cover and another move survives. Mist accepts the fatal offer **3** times and declines **30**. Nineteen turns include hidden rook cover. These are correlated, heterogeneous decisions, not independent estimates of one probability.

Most instructive: in `o7pac9wt` it declines Kxg7 at plies 48, 50, 52, 54, 56, 58 and 60, including taking with a knight at 48 instead. Only h6–h7, attacking the king and leaving one safe reply, induces Kxg7 at 62. A flat bait probability misses this transition. This is a reason to condition the exploit, not to abandon it.

## Suggested next step for your deception gate

Keep the existing constant-probability candidate as control. A subsequent response model can condition on king already threatened, visible escape count/quality, other pieces able to take the offer, bait type/value, previous refusals, and concealed cover across our belief particles. Pair that with a preparation term for rook batteries and useful pawn breaks toward the likely king region. The opening/castling tendency is useful prior information; update it with observations rather than assuming the king remains there forever.

The refreshed pure-network Mist replica is the right available behavior proxy to inspect. Verify its responses to **declines as well as takes**, restoring recurrent state from the whole observation history. If these games trained the replica, call this a diagnostic and use subsequent games for prediction validation. It does not need to generalize to every other team to earn a Mist specialist experiment. A small control panel should quantify the matchup cost, not require universal improvement.

**Artifacts you can reuse now:**

- [41 tactical decisions](../astra-submissions/analysis/mist-v1-20261009/tactical-cases.json): our eight final losses and the 33 bait opportunities, with negative labels and exact decision plies.
- [Full anatomy](../astra-submissions/analysis/mist-v1-20261009/anatomy.json) and [summary](../astra-submissions/analysis/mist-v1-20261009/summary.json).
- [Offline analyzer](../astra-submissions/tools/analyze_mist.py): validates all **4,788 frames**, both views, castling/EP and terminal rules with the course referee. Safe alternatives are retrospective truth labels, never deployment inputs.
- Frozen cache `/media/henrytan/seagate/iamavirus/astra/corpus/mist-v1-20261009/`; all replay bytes reused your mirror, with hashes. No duplicate downloads.

One defensive example worth feeding your belief-fusion gate: `gjmn6za2`, Qb3 at ply 41, visible to us at frame 42 and stationary through our fatal Kf8–g8 at ply 54. The remembered queen's diagonal alone would reject that king move. There were 18 surviving alternatives.
