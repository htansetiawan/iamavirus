"""Deep RL for v18: regularised PPO in the batched C++ simulator, with a training-only
true-board critic and a league of network opponents (reports/Deep RL for Fog of War
chess.md; GYM.md 3.8).

    python -m learning.rl_train --config learning/configs/rl_v18.yaml --output checkpoints/rl-v18

Per iteration: G games run in `batch_env` (C++ rules and the bot's own input features).
The learner plays one side of every game from its fogged views; the other side is a
league member (the imitation reference, team replicas, frozen learner snapshots), all
batched on the GPU. At each learner decision we keep the recurrent state before the
decision's new observation events, those events, the legal candidates, the sampled
move, its log-probability under the learner and under the reference, and the true board.

Loss (actor):   PPO-clip on GAE advantages
              + alpha * KL(pi || pi_ref)   (MMD-style pull to the imitation policy)
              - beta * entropy
Critic: V(true board) from learning/critic.py, fine-tuned on lambda-returns (gamma = 1,
reward +1 / 0 / -1 at the end of the game). Gradients flow through the decision's own
observation steps (truncated at the stored state, as in stored-state recurrent RL).
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml

from .batch_env import BatchEnv
from .critic import Critic, planes_from_board
from .model import FogPolicy, masked_log_softmax
from .pretrain import load_model


@dataclass
class Member:
    name: str
    model: FogPolicy
    weight: float


def load_policy(path: str, device) -> FogPolicy:
    model, _ = load_model(Path(path), device)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model


class Rollout:
    """Collects learner transitions from G parallel games."""

    def __init__(self, env: BatchEnv, learner: FogPolicy, reference: FogPolicy, league: list[Member], device, rng):
        self.env, self.learner, self.reference, self.league, self.device, self.rng = env, learner, reference, league, device, rng
        G = env.n
        H = learner.hidden
        self.h_learner = torch.zeros(G, H, device=device)       # learner's state for its side
        self.h_ref = torch.zeros(G, H, device=device)           # reference's state for the learner's side
        self.h_opp = torch.zeros(G, H, device=device)           # opponent's state for its side
        self.learner_side = np.zeros(G, np.int64)
        self.opponent = [None] * G
        self.open_index = [[] for _ in range(G)]                # indices of this game's transitions
        for i in range(G):
            self._assign(i)

    def _assign(self, i):
        self.learner_side[i] = self.rng.randrange(2)
        weights = [m.weight for m in self.league]
        self.opponent[i] = self.rng.choices(range(len(self.league)), weights=weights)[0]
        self.h_learner[i].zero_()
        self.h_ref[i].zero_()
        self.h_opp[i].zero_()
        self.open_index[i] = []

    @torch.no_grad()
    def _advance(self, model, h, games, side_of):
        """Runs `model` over each game's pending observation events for the side about to move.
        Returns per-game (spatial after the last event) and the stacked events for storage."""
        events = []
        for i in games:
            planes, scalars = self.env.take_events(i, side_of(i))
            events.append((planes, scalars))
        return events

    def collect(self, target: int, temperature: float = 1.0):
        env, dev = self.env, self.device
        trans = []          # dicts per learner decision
        results = []        # (opponent index, learner score)
        decisions = 0
        # Games continue across iterations; their earlier decisions were bootstrapped by the
        # critic at the end of the last batch, so only this batch's indices are tracked.
        self.open_index = [[] for _ in range(env.n)]
        while decisions < target:
            movers = np.array([env.side_to_move(i) for i in range(env.n)])
            learner_games = [i for i in range(env.n) if movers[i] == self.learner_side[i]]
            opp_games = [i for i in range(env.n) if movers[i] != self.learner_side[i]]
            actions = np.full(env.n, -1, np.int32)
            # --- learner (and the reference shadowing it) ---
            if learner_games:
                evs = [env.take_events(i, int(movers[i])) for i in learner_games]
                idx = torch.tensor(learner_games, device=dev)
                h_before = self.h_learner[idx].clone()
                hl, sp = self._run_events(self.learner, self.h_learner, idx, evs)
                hr, spr = self._run_events(self.reference, self.h_ref, idx, evs)
                cands = [env.candidates(i) for i in learner_games]
                cf, ct, cp, mask = self._pack(cands)
                with torch.no_grad():
                    logits, _ = self.learner.score(hl, sp, cf, ct, cp)
                    ref_logits, _ = self.reference.score(hr, spr, cf, ct, cp)
                    logp = masked_log_softmax(logits / temperature, mask)
                    ref_logp = masked_log_softmax(ref_logits, mask)
                    choice = torch.multinomial(logp.exp().nan_to_num(0.0) + 1e-12 * mask, 1).squeeze(1)
                for k, i in enumerate(learner_games):
                    n = int(mask[k].sum())
                    a = int(choice[k])
                    actions[i] = a
                    board = env.board(i)
                    trans.append({"game": i, "h": h_before[k].cpu(), "events": evs[k], "cand": (cands[k][0], cands[k][1], cands[k][2]),
                                  "action": a, "old_logp": float(logp[k, a]), "ref_logp": ref_logp[k, :n].cpu(),
                                  "board": board, "side": int(self.learner_side[i]), "reward": 0.0, "done": False})
                    self.open_index[i].append(len(trans) - 1)
                decisions += len(learner_games)
            # --- opponents, grouped by league member ---
            by_member = {}
            for i in opp_games:
                by_member.setdefault(self.opponent[i], []).append(i)
            for mi, games in by_member.items():
                evs = [env.take_events(i, int(movers[i])) for i in games]
                idx = torch.tensor(games, device=dev)
                member = self.league[mi].model
                ho, spo = self._run_events(member, self.h_opp, idx, evs)
                cands = [env.candidates(i) for i in games]
                cf, ct, cp, mask = self._pack(cands)
                with torch.no_grad():
                    logits, _ = member.score(ho, spo, cf, ct, cp)
                    logp = masked_log_softmax(logits, mask)
                    choice = torch.multinomial(logp.exp().nan_to_num(0.0) + 1e-12 * mask, 1).squeeze(1)
                for k, i in enumerate(games):
                    actions[i] = int(choice[k])
            status = env.step_all(actions)
            for i in range(env.n):
                if status[i] != 0:
                    side = self.learner_side[i]
                    score = 0.5 if status[i] == 3 else (1.0 if (status[i] == 1) == (side == 0) else 0.0)
                    if self.open_index[i]:
                        last = trans[self.open_index[i][-1]]
                        last["reward"] = 2.0 * score - 1.0
                        last["done"] = True
                    results.append((self.opponent[i], score))
                    env.reset(i)
                    self._assign(i)
        return trans, results

    def _run_events(self, model, H, idx, evs):
        """Steps `model` through each game's events (1-2), updating H[idx] in place."""
        dev = self.device
        h = H[idx]
        kmax = max(len(e[0]) for e in evs)
        spatial = torch.zeros(len(evs), model.channels, 8, 8, device=dev)
        for t in range(kmax):
            sel = [k for k, e in enumerate(evs) if len(e[0]) > t]
            if not sel:
                continue
            planes = torch.from_numpy(np.stack([evs[k][0][t] for k in sel])).to(dev)
            scal = torch.from_numpy(np.stack([evs[k][1][t] for k in sel])).to(dev)
            with torch.no_grad():
                nh, sp, _, _ = model.observe(planes, scal, h[sel])
            h = h.clone()
            h[sel] = nh
            spatial[sel] = sp
        H[idx] = h
        return h, spatial

    def _pack(self, cands):
        dev = self.device
        M = max(1, max(len(c[0]) for c in cands))
        B = len(cands)
        cf = torch.zeros(B, M, dtype=torch.long)
        ct = torch.zeros(B, M, dtype=torch.long)
        cp = torch.zeros(B, M, dtype=torch.long)
        mask = torch.zeros(B, M, dtype=torch.bool)
        for k, (f, t, p) in enumerate(cands):
            n = len(f)
            cf[k, :n] = torch.from_numpy(f.astype(np.int64))
            ct[k, :n] = torch.from_numpy(t.astype(np.int64))
            cp[k, :n] = torch.from_numpy(p.astype(np.int64))
            mask[k, :n] = True
        return cf.to(dev), ct.to(dev), cp.to(dev), mask.to(dev)


def gae(trans, values, gamma, lam):
    """Per game: advantages and lambda-returns over the learner's decisions (reward only at the end)."""
    adv = np.zeros(len(trans), np.float32)
    ret = np.zeros(len(trans), np.float32)
    by_game = {}
    for k, t in enumerate(trans):
        by_game.setdefault((t["game"], id(t.get("episode", None))), []).append(k)
    # episodes: split each game's sequence at done flags
    episodes, current = [], {}
    for k, t in enumerate(trans):
        current.setdefault(t["game"], []).append(k)
        if t["done"]:
            episodes.append(current.pop(t["game"]))
    episodes += [seq for seq in current.values()]   # unfinished: bootstrap from the critic
    for seq in episodes:
        next_value, running = 0.0, 0.0
        last_done = trans[seq[-1]]["done"]
        if not last_done:
            next_value = float(values[seq[-1]])
        for pos in range(len(seq) - 1, -1, -1):
            k = seq[pos]
            r = trans[k]["reward"]
            nv = next_value if pos == len(seq) - 1 else float(values[seq[pos + 1]])
            if pos == len(seq) - 1 and last_done:
                nv = 0.0
            delta = r + gamma * nv - float(values[k])
            running = delta + gamma * lam * running
            adv[k] = running
            ret[k] = running + float(values[k])
    return adv, ret


def critic_values(critic, trans, device):
    xs = np.stack([planes_from_board(t["board"], t["side"]) for t in trans]).astype(np.float32)
    out = []
    with torch.no_grad():
        for i in range(0, len(xs), 8192):
            out.append(critic(torch.from_numpy(xs[i:i + 8192]).to(device)).float().cpu())
    return torch.cat(out).numpy(), xs


def update(learner, critic, opt_a, opt_c, trans, adv, ret, xs, cfg, device):
    n = len(trans)
    order = np.random.permutation(n)
    adv_t = torch.from_numpy((adv - adv.mean()) / (adv.std() + 1e-8))
    stats = {"kl_ref": [], "entropy": [], "clip_frac": [], "approx_kl": [], "value_loss": []}
    mb = cfg["minibatch"]
    for epoch in range(cfg["epochs"]):
        np.random.shuffle(order)
        for s in range(0, n, mb):
            ids = order[s:s + mb]
            batch = [trans[k] for k in ids]
            h = torch.stack([t["h"] for t in batch]).to(device)
            # replay each decision's 1-2 events with gradients
            kmax = max(len(t["events"][0]) for t in batch)
            spatial = torch.zeros(len(batch), learner.channels, 8, 8, device=device)
            for e in range(kmax):
                sel = [k for k, t in enumerate(batch) if len(t["events"][0]) > e]
                planes = torch.from_numpy(np.stack([batch[k]["events"][0][e] for k in sel])).to(device)
                scal = torch.from_numpy(np.stack([batch[k]["events"][1][e] for k in sel])).to(device)
                nh, sp, _, _ = learner.observe(planes, scal, h[sel])
                h = h.clone()
                h[sel] = nh
                spatial = spatial.clone()
                spatial[sel] = sp
            M = max(len(t["cand"][0]) for t in batch)
            cf = torch.zeros(len(batch), M, dtype=torch.long)
            ct = torch.zeros(len(batch), M, dtype=torch.long)
            cp = torch.zeros(len(batch), M, dtype=torch.long)
            mask = torch.zeros(len(batch), M, dtype=torch.bool)
            ref = torch.full((len(batch), M), -1e9)
            for k, t in enumerate(batch):
                f, to, p = t["cand"]
                m = len(f)
                cf[k, :m] = torch.from_numpy(f.astype(np.int64))
                ct[k, :m] = torch.from_numpy(to.astype(np.int64))
                cp[k, :m] = torch.from_numpy(p.astype(np.int64))
                mask[k, :m] = True
                ref[k, :m] = t["ref_logp"]
            cf, ct, cp, mask, ref = cf.to(device), ct.to(device), cp.to(device), mask.to(device), ref.to(device)
            logits, _ = learner.score(h, spatial, cf, ct, cp)
            logp_all = masked_log_softmax(logits, mask)
            act = torch.tensor([t["action"] for t in batch], device=device)
            logp = logp_all.gather(1, act.unsqueeze(1)).squeeze(1)
            old = torch.tensor([t["old_logp"] for t in batch], device=device)
            ratio = torch.exp(logp - old)
            a = adv_t[ids].to(device)
            clip = cfg["clip"]
            actor = -torch.min(ratio * a, torch.clamp(ratio, 1 - clip, 1 + clip) * a).mean()
            p = logp_all.exp() * mask
            safe_logp = logp_all.masked_fill(~mask, 0.0)
            kl_ref = (p * (safe_logp - ref.masked_fill(~mask, 0.0))).sum(1).mean()
            entropy = -(p * safe_logp).sum(1).mean()
            loss = actor + cfg["kl_ref_coef"] * kl_ref - cfg["entropy_coef"] * entropy
            opt_a.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(learner.parameters(), cfg["grad_clip"])
            opt_a.step()
            # critic
            v = critic(torch.from_numpy(xs[ids]).to(device))
            vloss = F.mse_loss(v.float(), torch.from_numpy(ret[ids]).to(device))
            opt_c.zero_grad(set_to_none=True)
            vloss.backward()
            opt_c.step()
            with torch.no_grad():
                stats["kl_ref"].append(float(kl_ref))
                stats["entropy"].append(float(entropy))
                stats["clip_frac"].append(float(((ratio - 1).abs() > clip).float().mean()))
                stats["approx_kl"].append(float((old - logp).mean()))
                stats["value_loss"].append(float(vloss))
    return {k: round(float(np.mean(v)), 4) for k, v in stats.items() if v}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--iterations", type=int, default=None)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())["rl"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(cfg.get("seed", 1))
    rng = random.Random(cfg.get("seed", 1))
    learner, payload = load_model(Path(cfg["init"]), device)
    learner.train()
    reference = load_policy(cfg["init"], device)
    league = [Member("reference", reference, cfg["league"].get("reference", 1.0))]
    for name, path in (cfg["league"].get("replicas") or {}).items():
        league.append(Member(name, load_policy(path, device), cfg["league"].get("replica_weight", 1.0)))
    critic = Critic().to(device)
    critic.load_state_dict(torch.load(cfg["critic_init"], map_location=device, weights_only=False)["state_dict"])
    opt_a = torch.optim.Adam(learner.parameters(), lr=cfg["lr"])
    opt_c = torch.optim.Adam(critic.parameters(), lr=cfg["critic_lr"])
    env = BatchEnv(cfg["games"], max_plies=cfg["max_plies"], threads=cfg.get("env_threads", 1))
    roll = Rollout(env, learner, reference, league, device, rng)
    args.output.mkdir(parents=True, exist_ok=True)
    log = open(args.output / "rl_log.jsonl", "a")
    iterations = args.iterations or cfg["iterations"]
    snapshot_every = cfg["league"].get("snapshot_every", 5)
    for it in range(1, iterations + 1):
        t0 = time.time()
        trans, results = roll.collect(cfg["rollout_decisions"], cfg.get("temperature", 1.0))
        t1 = time.time()
        values, xs = critic_values(critic, trans, device)
        adv, ret = gae(trans, values, cfg["gamma"], cfg["lambda"])
        stats = update(learner, critic, opt_a, opt_c, trans, adv, ret, xs, cfg, device)
        t2 = time.time()
        by = {}
        for mi, sc in results:
            by.setdefault(league[mi].name, []).append(sc)
        record = {"iteration": it, "decisions": len(trans), "games_finished": len(results),
                  "rollout_seconds": round(t1 - t0, 1), "update_seconds": round(t2 - t1, 1),
                  "decisions_per_second": round(len(trans) / max(t1 - t0, 1e-6), 1),
                  "score_vs": {k: [round(float(np.mean(v)), 3), len(v)] for k, v in by.items()}, **stats}
        log.write(json.dumps(record) + "\n")
        log.flush()
        print(json.dumps(record), flush=True)
        torch.save({"state_dict": learner.state_dict(), "model_config": learner.size_config,
                    "architecture": learner.architecture, "feature_version": payload.get("feature_version"),
                    "action_version": payload.get("action_version"), "rules_fingerprint": payload.get("rules_fingerprint"),
                    "step": it, "epoch": 0, "rl": cfg}, args.output / "latest.pt")
        if it % snapshot_every == 0:
            snap = load_policy(str(args.output / "latest.pt"), device)
            league.append(Member(f"snapshot-{it}", snap, cfg["league"].get("snapshot_weight", 1.0)))
            torch.save(torch.load(args.output / "latest.pt", weights_only=False), args.output / f"snapshot-{it}.pt")
    log.close()


if __name__ == "__main__":
    main()
