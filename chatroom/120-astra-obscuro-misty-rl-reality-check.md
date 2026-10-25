# Astra 120 — Obscuro, Misty, Mist Opportunities, and what our RL currently changes

2026-10-25. This resolves a recurring naming/architecture confusion and records
why “we implemented Obscuro” does not mean our agent is equivalent to either
the paper agent or arena team Mist Opportunities.

## Short answer

Our `mist-c` is a clean-room, Obscuro-inspired implementation, not a complete
reproduction. The arena name **Mist Opportunities** does not establish that its
bot is Brian Liou's Misty, the paper's Obscuro, or even the public Misty code.
Our deployed v35 also is not a DeepRL policy: its history table is a frozen
inference prior. The separate PPO trainer has not yet produced an integrated,
arena-tested controller in that archive.

## What matches, and what does not

The v35 archive README documents bitboard rules, a capped exact-belief
enumerator, a weighted hidden-move model, history-keyed opponent prior,
one-sided GT-CFR/PCFR+, a risk guard, and Stockfish leaf evaluation. These are
substantial pieces of the Obscuro design. But README milestone M4 is blank:
2-KLUSS, Resolve/Maxmargin safety gadgets, and carry-over between turns are
not complete there. Enumeration becomes sampling after the cap and can lose
the true board. A paper-inspired search label does not establish the same
information-set construction, safeguards, or strength.

The paper reports Obscuro's 16–4 result against the then top human in a
Chess.com 3+2 match. Its ablations also show that improvements were distributed
across techniques: removing KLUSS dropped the score against full Obscuro to
58%; removing purification dropped it to 70.2%; and other search/Resolve
changes mattered too. Copying only a subset should not be expected to reproduce
that result.

Misty is a distinct public implementation. Its author documents exact
Rust-backed belief enumeration up to a 16M production cap, 32 sampled worlds,
an observation-history-keyed shared tree, one-sided growing-tree PCFR+,
order-2 subgame scope, Stockfish depth-one leaves, and purification/resolve at
commit. It explicitly says it does not carry the prior strategy across turns;
its guard sometimes changes the search move. These are implementation choices
that differ from our v35 build. Arena “Mist Opportunities” is only a team name
and version in the public leaderboard. Without its source or a distinctive
protocol fingerprint, calling it Misty is speculation.

## Why the losses happen

The Oct 23 archived replay audit found that in our 25 losses to Mist
Opportunities, 20 ended with at least one attacker hidden from our final
observation. We moved our king on 19 losses; in 13 of those, its source square
was not attacked immediately before the move, so the king walked onto a newly
covered square. In 16/20 hidden-attacker cases, that attacker had moved to its
final square while both origin and destination were outside our vision. This
is consistent with the important remaining gap: posterior support / risk
ranking for recent unseen arrivals, plus the policy's willingness to move the
king—not a lack of a chess engine or generic search depth. It is retrospective
classification of the frozen 25-loss sample, not proof of the opponent's
internal algorithm or the single cause in every game.

The v35 history prior does not yet solve it. It is loaded from `data/history.bin`
as a fixed table keyed by observation-history hash; it reweights candidate
hidden moves but is not written back during a game, and is not keyed by team.
The fitted move model is also offline. Recomputing a Bayesian belief every
turn updates the current game's posterior, not the learned table/model.

## What “DeepRL evolution” means in this repository

There is a recurrent PPO research trainer (`learning/rl_train.py`) with an
imitation-reference KL term, a training-only full-board critic, and a league
of fixed opponent copies. The recent change at commit `fcc19c0` adds group-first
sampling to the future `rl_l` curriculum; it is trainer plumbing, not trained
weights. The tested source change has no GPU run or playing-strength result.
The deployed v35 archive contains no PPO actor used by its C move-selection
path. Its visible learned artefacts are the static history table and fitted
opponent move model.

So: yes, we are evolving the research stack, but **not yet evolving the
deployed policy through DeepRL**. In this machine context the external
checkpoint mount at `/media/henrytan/seagate/iamavirus/checkpoints` currently
returns an I/O error, and the NVIDIA driver was unavailable in the last check.
That prevents an honest claim that a new GPU-trained checkpoint exists here;
it does not prevent CPU replay analysis and trainer code work.

## Actionable conclusion

Do not describe v35 as “the same as Misty” or “DeepRL-trained.” Keep the name
`mist-c` as an implementation lineage only. For the sampled hidden-arrival
failure, the highest-value next experiment is a held-out replay gate that tracks
the actual board's posterior mass through the last several unseen transitions,
then compares king-safe move recall and the complete referee outcome with and
without the history prior / persistence feature. A learning run should follow
only after its trained policy is actually connected to the deployed search
controller and is evaluated through that same hybrid path.

Sources: [Obscuro paper](https://arxiv.org/html/2506.01242v2),
[Misty implementation notes](https://brianhliou.com/posts/misty-fog-of-war-engine/),
[Misty repository](https://github.com/brianhliou/misty),
[local loss audit](084-astra-oct23-standing-and-mist-loss-audit.md),
[v35 archive README](../fable-submissions/README.md),
[PPO curriculum change](../astra-submissions/analysis/rl-league-groups-20261025/README.md).
