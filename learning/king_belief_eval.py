import json, random, sys
from pathlib import Path
import torch, torch.nn.functional as F
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from learning import dataset as ds
from learning.pretrain import burn_in, run_sequence, load_model, to_device
manifest = json.load(open(Path.home() / "git/iamavirus/data/manifests/v4.json"))
episodes = ds.load_episodes(Path.home() / "git/iamavirus" / manifest["shards"]["test"], None)
device = torch.device("cuda")
for ckpt in sys.argv[1:]:
    model, payload = load_model(Path(ckpt), device); model.eval()
    n = 0; mass_sum = 0.0; top1 = 0; low = 0
    by_phase = {"<30": [0, 0.0], "30-79": [0, 0.0], "80+": [0, 0.0]}
    rng = random.Random(0)
    with torch.no_grad():
        for start in range(0, len(episodes), 16):
            group = episodes[start:start + 16]
            longest = max(len(e.actor.observations) for e in group)
            for ws in range(0, longest, 64):
                starts = [min(ws, max(len(e.actor.observations) - 1, 0)) for e in group]
                batch = to_device(ds.make_batch(group, 64, rng, starts), device)
                D = batch["decision_seq"].shape[0]
                if D == 0: continue
                h0 = burn_in(model, batch)
                _, _, beliefs, _ = run_sequence(model, batch["planes"], batch["scalars"], batch["window_lengths"], h0)
                seq, step = batch["decision_seq"], batch["decision_step"]
                bl = beliefs[seq, step]                      # [D,64,7]
                classes = batch["belief_classes"]            # [D,64]
                hidden = batch["belief_mask"] & batch["belief_valid"].unsqueeze(1)
                pk = F.softmax(bl.float(), -1)[..., 5] * hidden
                is_king = (classes == 5)
                king_hidden = (is_king & hidden).any(1)
                total = pk.sum(1).clamp(min=1e-9)
                for i in torch.nonzero(king_hidden).flatten().tolist():
                    sq = int(torch.nonzero(is_king[i])[0])
                    m = float(pk[i, sq] / total[i])
                    n += 1; mass_sum += m; top1 += int(int(pk[i].argmax()) == sq); low += int(m < 0.2)
                    # event index within the window -> rough ply = 2 * decision index; use window start + step
                    ply = 2 * (starts[int(seq[i])] + int(step[i])) // 2
                    key = "<30" if ply < 30 else ("30-79" if ply < 80 else "80+")
                    by_phase[key][0] += 1; by_phase[key][1] += m
    print(f"{payload.get('architecture')} step {payload.get('step')}: hidden-king decisions {n}; mass on the true king square {mass_sum/n:.3f}; top-1 square {100*top1/n:.1f}%; < 20% mass {100*low/n:.1f}%; by event index " +
          ", ".join(f"{k} {v[1]/max(v[0],1):.3f} (n={v[0]})" for k, v in by_phase.items()))
