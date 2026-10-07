# Astra: data, compression, retrieval, and GPU purpose

2026-10-07. The user asked whether we keep collecting/curating data, why we need
the GPU, and whether DC-AE, VQ-VAE or residual VQ can give a compact runtime
predictor. The detailed contract is
[compact-experience-learning.md](../astra-submissions/specs/compact-experience-learning.md).

The exact board format is already small: 32 bytes losslessly with four bits per
square, including hidden separately from empty. Use bitboards for computation;
learned compression should summarize observation history and uncertainty. Our
deployed network already has a 256-state GRU. Compare a smaller recurrent student
and a retrieval embedding before quantizing recurrent memory. Test grouped VQ
and residual VQ against a continuous/int8 baseline; preserve king-danger recall,
not merely reconstruction of mostly empty squares. DC-AE's large-image spatial
compression is a less direct fit for 8-by-8 categorical boards.

I implemented `astra-submissions/tools/experience_index.py`: lossless packing,
history prefix keys, last-seen memory, fixed split/duplicate checks, actor-only
storage, and train-only indexed retrieval with a bounded top-k heap. Six contract
tests pass. It is an offline baseline, not yet a learned embedding or runtime
policy. The full v2 build is on Seagate and temporarily SIGSTOPed at PID 3801137
after learning that the new Fable-vs-Astra real-clock lanes took cores 2-5.
Please release a core when available and notify me; I will resume that exact job.

At my audit: raw store 3,572 accepted games / 288,288 frames, v2 training manifest
3,258 games / 211,999 training decisions. The monitor is active; 26 cached games
were newer than the raw corpus. No broad ingestion/curation/training job was
active then. Please own targeted expansion/validation (Duck v5, TA A/S, top bots,
both colors/outcomes), reuse monitor cache, and report current curated counts.
I own the index and representation experiments. This proposed division awaits
your acknowledgment; it is not a claim that curation is already continuous.

GPU use is training/distillation and eventually batched rollout inference.
Collection, correctness, search and the index are CPU work. Keep the current
vLLM service running; wait until it is free. The deployed model remains CPU-only.
The compression proposal has not produced a new model or an Elo estimate.

Continuation work also progressed: nine suites and 18,625 referee checks pass;
three replay probes remove invalid previous-mover worlds but show mixed collapse
and truth-support results. The new modern-v12 harness with flags off matches all
40 baseline decisions. The action gate awaits CPU availability; see
[the experiment report](../astra-submissions/analysis/continuation-evidence/README.md).

Upload tracking: user reports both archives submitted. Monitor confirmed arena
v11 after the Astra a5f806 upload; your table maps your 68a890 candidate to v12.
The ZIP labels remain separate. New Astra packaging must now inspect your latest
numbered archives again rather than reuse our immutable v12 filename.
