# Compact experience learning and retrieval

2026-10-07. Astra's response to the user's request for a data search engine,
DC-AE/VQ-VAE/residual-VQ experiments, and a predictor small enough for the arena.
This is a research contract, not a claim that compression improves playing strength.

## What exists, and what the GPU is for

At the 20:38 UTC audit the shared raw store contained **3,572 accepted games and
288,288 frames**. The most recent raw download completed at 19:55 UTC. The live
Astra monitor had 66 cached replays, 26 of them outside that raw snapshot. It
continues every five minutes and caches new IAmAVirus games. The broad ingest
batch was finished; no ingest, curation, pretraining or PPO process was running
at the audit. A downloaded monitor replay is not automatically a validated,
labelled training example.

Fable's frozen v2 dataset contains 3,258 games: 2,607 training, 326 validation,
325 test; 211,999 / 25,989 / 26,010 decisions respectively. The current deployed
model remains Stage A v1. The existing `learning/model.py` is already recurrent:
64 convolution channels, four residual blocks, a 256-dimensional GRU, and
policy, danger, belief and value heads. We should build on it and measure it.

The GPU is for parallel minibatch training, teacher/student distillation and,
later, batched policy inference during simulator rollouts. Validation, collection,
index construction and the present engine run on CPU. More GPU memory does not
fix slow Python simulation or a wrong training target. The current vLLM service
keeps the GPU; no training or opportunistic VRAM allocation starts until it is
free. The arena uses CPU inference; no runtime API search or GPU is proposed.

## Three different meanings of compression

| Representation | Cost | What it preserves |
|---|---:|---|
| One full board or observation, 4 bits per square | 32 bytes | All 64 categorical symbols exactly, including distinct hidden/empty |
| Twelve piece bitboards | 96 bytes, plus visibility/state | Fast bitwise move generation and attacks; intentionally redundant relative to packed storage |
| Current GRU state, 256 float32 values | 1,024 bytes | A learned, lossy summary of permitted history |
| Proposed 128-dimensional int8 state | 128 bytes, plus quantization metadata | Quantized learned history; accuracy must be measured |
| Proposed grouped VQ state | 8 code bytes, plus shared codebooks | Eight 16-dimensional groups with 256 entries each |
| Proposed two-stage residual VQ state | 16 code bytes, plus shared codebooks | Coarse code plus residual code for each of the eight groups |

The 32-byte format is for storage; it is not a complete game state. Side,
castling, EP, counters and repetition/history context need additional fields.
A board-sized float latent can be larger than the original packed board.
The useful learned compression target is **history and uncertainty**, not
just the current 64-square diagram.

For the concrete 128-dimensional grouped design, eight independent 256-by-16
FP16 codebooks cost 64 KiB; two residual stages cost 128 KiB. Index codes are
therefore cheap per experience, but the encoder, codebooks, heads and retrieval
graph all count toward deployment cost. These are proposed sizes, not measured
model artifacts. Quantizing activations and quantizing weights are separate
experiments. Keeping an unquantized recurrent update while quantizing only the
retrieval key is the lowest-risk first learned-code variant.

Treat the board as an 8-by-8 categorical grid with piece and visibility channels.
Do not treat integer piece IDs as grayscale intensity or apply photographic
perceptual losses. A one-square error on a hidden rook can lose the game despite
excellent average reconstruction. Always retain exact visible squares, own
pieces, legal candidates and rule-derived constraints alongside the latent.
The latent proposes probabilities; it cannot overwrite those facts.

## CPU deliverable: searchable, packed experience

`../tools/experience_index.py` now implements:

- Lossless 32-byte observation packing; unknown is a distinct code.
- Packed legal moves, own rights/EP, last observed occupancy and observation age.
- A SHA-256 fingerprint of observation/phase/ply and preceding own actions.
  The action being predicted and future observations never enter its prefix.
  This source schema has no clocks, so the fingerprint is not a complete runtime
  information set or a proof of Markov sufficiency.
- Preserved source manifests/checksums and whole-game splits. Both seats and
  exact duplicate complete trajectories are checked for split consistency.
- Separate actor records: true boards, hidden opponent moves, outcomes and
  danger targets are not copied into the index. Game/event IDs allow a later
  offline join to the existing supervised targets.
- Indexed exact recorded-prefix lookup, plus a bounded baseline query by side,
  own king square and own piece count, followed by categorical observation
  distance and a top-k heap. It searches training records only. The query can
  exclude the entire source trajectory, including duplicate games.

The baseline candidate pool is capped before distance calculation; reranking
costs O(M log k), M <= the configured budget. SQLite supplies B-tree lookups.
This is **not** a global nearest-neighbor search or a recall guarantee: large
context buckets are explicitly marked truncated. Current-view similarity is
not equivalence of histories. The full prefix key and last-seen memory are
retained so we can measure that failure rather than erase it.

The six initial tests cover all-symbol round trips, unknown/empty distinction,
temporal input isolation, last-seen memory, promotion coding, training-only
retrieval, query caps, duplicate exclusion, and duplicate-split rejection.
The full v2 build is on Seagate. Its execution status is recorded in the
experiment report; do not mistake a partial database for a finished artifact.

After a validated embedding exists, compare exact vector search against HNSW
and an inverted codebook index on the same frozen queries. Measure recall@k,
p95/p99 latency, memory, and downstream move ranking. HNSW's favorable empirical
scaling is not a worst-case logarithmic guarantee. A tiny frozen opening/trap
table may be useful in the arena; the full research corpus need not ship.

## Data acquisition and curation contract

Fable is asked to own broad ingestion and curation; Astra owns the continuing
IAmAVirus monitor, representation/index work, and independent belief experiments.
This division is a coordination request until acknowledged in the ledger.
Reuse cached replays before GET requests. Keep requests sequential and paced,
honor Retry-After, and append exact API metadata and source checksums.

Next data strata: Duck **v5 separately from v4**; TA A and S; top opponents;
both colors; both wins and losses; and new arena v11/v12 games under the shared
archive mapping. Include ordinary positions alongside tactical failures to
retain the natural error base rate. Do not train only on losses or duplicate
opening states until they dominate the minibatches.

Validate every replay by reconstructing board, observations, legality and
termination under pinned rules. Quarantine mismatches. Derive actor histories
and privileged labels separately. Keep final decided frames out of live actor
inputs. Labels should include hidden-piece distributions, actual opponent
action, all-candidate immediate king danger, material exposure, promotions and
whether a threat is invisible to the opponent in each labelled true state.

Split whole games and exact duplicate trajectories before cutting windows.
The current v2 split is frozen for an initial representation comparison; newer
games are held for a separate chronological evaluation until a fresh manifest
is declared. Future train/dev/test manifests may reuse historical data only
with explicit split lineage. Add opponent-version holdouts and opponent-balanced
weights; publish counts and metrics per color and target opponent. Current
leaderboard Elo is not a historical per-decision skill label.

For synthetic data, use rules-exact simulation, frozen opponent versions,
multiple seeds, full observation histories and explicit provenance. Restarting
from a true board alone does not recreate either player's hidden information.
Store recurrent states, own histories and repetition context when branching.
Public demonstrations belong in supervised losses; they are not fresh PPO
samples. Counterfactual danger labels are labels, not actor inputs.

## Learner experiments, in order

1. **Continuous recurrent baseline.** Measure the existing model and a smaller
   student on the same permitted histories. Predict hidden occupancy, opponent
   choices, all-candidate danger and value. Distill belief-aware search rankings
   where available; never present a full-information teacher's choices as if
   the actor had the same information. Fit calibration on natural-frequency
   validation data. Keep danger log-only until its operating point passes.
2. **Retrieval latent.** Add a 128-dimensional history projection; use ordinary
   numeric quantization first. Retrieve train-only analogues and evaluate whether
   they improve hidden-attacker likelihood or legal-move ranking over the model
   alone. Teacher target embeddings can be privileged during supervised training,
   but the query encoder and runtime input must be observation-only.
3. **VQ/RVQ ablation.** Compare continuous, grouped VQ, and two-stage residual VQ
   under identical training data, steps and parameter/latency budgets. Start by
   quantizing the retrieval representation rather than every recurrent update.
   Include task losses and codebook occupancy diagnostics. A reconstruction-only
   win earns no policy claim. If rare tactical information degrades, increase
   capacity or reject the bottleneck.
4. **Small CPU predictor.** Export the selected encoder and heads, try int8
   weights/activations where supported, and test ONNX/Python/C++ numerical and
   decision parity. Invoke once per observation/root decision, not at every
   alpha-beta node. A compact model can rerank a few moves or weight opponent
   transitions. Do not multiply its belief marginals into the particle posterior
   without accounting for reused evidence and joint legality.
5. **Simulator improvement and PPO.** Only after labels, inference and batched
   simulation are reliable, use league rollouts for policy improvement. Measure
   end-to-end throughput; do not reserve the GPU merely to wait for CPU sampling.

The first GPU pilot should run one control and one variant with a fixed step
budget, resumption checkpoints and measured memory/throughput. Choose batch
sizes from a short profiling run after the existing service releases the GPU.
Do not prescribe a 48-hour sweep before a short experiment shows learning.

## Gates and fail-fast criteria

- Zero actor leakage, codec errors, cross-split duplicate trajectories and
  Python/C++ input mismatches. Any such failure stops the experiment.
- Hidden-piece NLL/Brier and actual hidden-attacker probability, broken out
  by piece and phase. Empty-square accuracy alone is insufficient.
- Danger recall at a matched false-positive rate, calibrated probabilities,
  and precision/recall on rare fatal opportunities. No veto based on an
  uncalibrated 0.5 threshold.
- Retrieval recall versus an exact baseline, held-out task benefit, index size
  and CPU p95/p99 latency. A smaller code with worse tactical recall loses.
- A provisional <=5 ms p95 for one root inference and <=64 MiB deployed model
  plus optional retrieval memory, measured on the arena CPU profile. These are
  engineering targets, not observed results; worst-case clocks still need tests.
- Paired replay gates followed by 180+2 color-swapped matches and versioned arena
  results. Data-derived metric changes do not imply a numerical Elo gain.

## Research grounding

- [VQ-VAE: Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937)
  introduces learned discrete representations using vector quantization. Its
  reported applications are not evidence that a chess history bottleneck helps.
- [RQ-VAE: Autoregressive Image Generation using Residual Quantization](https://arxiv.org/abs/2203.01941)
  represents an image feature map with stacked residual codes. We propose testing
  that rate/capacity tradeoff for history embeddings; this is an extrapolation.
- [DC-AE: Deep Compression Autoencoder](https://arxiv.org/abs/2410.10733)
  targets efficient high-resolution image diffusion. Aggressive spatial
  downsampling is not directly motivated on an 8-by-8 board. Its residual-design
  ideas may help an encoder, but it is lower priority than a task-trained recurrent
  baseline and VQ comparison.
- [HNSW](https://arxiv.org/abs/1603.09320) supplies a graph-based approximate
  nearest-neighbor method to compare against exact and codebook retrieval after
  we have a useful embedding.

None of these papers establish a Fog-of-War strength improvement. The proposed
adaptation is our hypothesis, and the held-out tactical and match gates decide it.
