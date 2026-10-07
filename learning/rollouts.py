"""Fresh PPO trajectories from the simulator against a league of frozen opponents.

The learner's behaviour policy is the masked categorical policy sampled at
temperature 1; each decision stores the exact log-probability, the old value,
the candidate list and the truth-derived auxiliary labels. Opponent checkpoints
stay fixed for a whole game. The collector finishes every active game with the
same frozen actor before the batch is returned, so no episode spans an update.
"""
from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass, field

import numpy as np
import torch

from . import env, features, histories, labels, rules
from .model import FogPolicy, masked_log_softmax


@dataclass
class RolloutEpisode:
    """A learner's same-player trajectory plus everything PPO needs to replay it."""
    episode: histories.PlayerEpisode
    action_index: np.ndarray      # [K]
    old_log_prob: np.ndarray      # [K]
    old_value: np.ndarray         # [K]
    reward: np.ndarray            # [K]
    terminated: np.ndarray        # [K] bool: game ended after this transition
    rollout_cut: np.ndarray       # [K] bool: truncated by the collector
    bootstrap_value: float        # value used after a cut (0 when terminated)
    opponent: str
    seed: int


@dataclass
class League:
    """Opponent mixture: recent frozen checkpoint, older checkpoints, fixed bots."""
    recent: list[str] = field(default_factory=list)   # model keys
    older: list[str] = field(default_factory=list)
    fixed: list[str] = field(default_factory=lambda: ["capture-greedy", "uniform-random"])
    recent_share: float = 0.5
    older_share: float = 0.25
    fixed_share: float = 0.25

    def sample(self, rng: random.Random) -> str:
        draw = rng.random()
        pools = [(self.recent_share, self.recent), (self.older_share, self.older), (1.0, self.fixed)]
        acc = 0.0
        for share, pool in pools:
            acc += share
            if draw < acc and pool:
                return rng.choice(pool)
        for _, pool in pools:
            if pool:
                return rng.choice(pool)
        return "uniform-random"


class Collector:
    def __init__(self, learner: FogPolicy, models: dict[str, FogPolicy], device, league: League,
                 games_in_flight: int = 32, max_plies: int = 1000, cpp_nodes: int = 20000):
        self.learner = learner.eval()
        self.models = {"learner": learner} | models
        self.device = device
        self.league = league
        self.games_in_flight = games_in_flight
        self.max_plies = max_plies
        self.cpp_nodes = cpp_nodes

    # -- players -------------------------------------------------------------
    def make_opponent(self, kind: str, side: int, seed: int) -> env.Player:
        if kind == "uniform-random":
            return env.UniformRandomPlayer(side)
        if kind == "capture-greedy":
            return env.CaptureGreedyPlayer(side)
        if kind.startswith("cpp"):
            nodes = int(kind.split(":")[1]) if ":" in kind else self.cpp_nodes
            return env.CppEnginePlayer(side, seed, nodes)
        if kind in self.models:
            return env.NeuralPlayer(side, kind, learner=False)
        raise ValueError(f"unknown opponent {kind}")

    # -- batched inference -----------------------------------------------------
    @torch.no_grad()
    def run_observe(self, players: list[env.NeuralPlayer]) -> None:
        by_model: dict[str, list[env.NeuralPlayer]] = {}
        for player in players:
            by_model.setdefault(player.model_key, []).append(player)
        for key, group in by_model.items():
            model = self.models[key]
            planes = np.stack([p.observe_inputs()[0] for p in group])
            scalars = np.stack([p.tracker.scalars() for p in group])
            hidden = torch.stack([p.hidden if p.hidden is not None else torch.zeros(256, device=self.device)
                                  for p in group])
            nh, sp, _, value = model.observe(torch.from_numpy(planes).to(self.device),
                                             torch.from_numpy(scalars).to(self.device), hidden)
            for i, player in enumerate(group):
                player.hidden = nh[i]
                player.spatial = sp[i]
                player.last_value = float(value[i, 0])

    @torch.no_grad()
    def run_score(self, players: list[env.NeuralPlayer], rng: random.Random) -> dict[int, tuple[str, int, float]]:
        """Samples a move for each player; returns id(player) -> (uci, index, log_prob)."""
        out = {}
        by_model: dict[str, list[env.NeuralPlayer]] = {}
        for player in players:
            by_model.setdefault(player.model_key, []).append(player)
        for key, group in by_model.items():
            model = self.models[key]
            inputs = [p.score_inputs() for p in group]
            M = max(len(f) for f, _, _ in inputs)
            if M == 0:
                continue
            B = len(group)
            cf = np.zeros((B, M), dtype=np.int64)
            ct = np.zeros((B, M), dtype=np.int64)
            cp = np.zeros((B, M), dtype=np.int64)
            mask = np.zeros((B, M), dtype=bool)
            for i, (f, t, p) in enumerate(inputs):
                n = len(f)
                cf[i, :n], ct[i, :n], cp[i, :n], mask[i, :n] = f, t, p, True
            hidden = torch.stack([p.hidden for p in group])
            spatial = torch.stack([p.spatial for p in group])
            logits, _ = model.score(hidden, spatial, torch.from_numpy(cf).to(self.device),
                                    torch.from_numpy(ct).to(self.device), torch.from_numpy(cp).to(self.device))
            mask_t = torch.from_numpy(mask).to(self.device)
            log_probs = masked_log_softmax(logits / max(group[0].temperature, 1e-6), mask_t)
            probs = log_probs.exp().cpu().numpy()
            for i, player in enumerate(group):
                n = len(player.pending_candidates)
                if n == 0:
                    out[id(player)] = (None, -1, 0.0)
                    continue
                p = probs[i, :n].astype(np.float64)
                p = p / p.sum()
                index = int(rng.choices(range(n), weights=p)[0])
                out[id(player)] = (player.pending_candidates[index], index, float(np.log(max(p[index], 1e-30))))
        return out

    # -- collection -------------------------------------------------------------
    def new_game(self, seed: int, rng: random.Random) -> env.Game:
        opponent = self.league.sample(rng)
        learner_side = seed % 2   # colours alternate across seeds
        learner = env.NeuralPlayer(learner_side, "learner", learner=True)
        other = self.make_opponent(opponent, learner_side ^ 1, seed * 7919 + 1)
        players = (learner, other) if learner_side == 0 else (other, learner)
        kinds = ("learner", opponent) if learner_side == 0 else (opponent, "learner")
        return env.Game(seed, players[0], players[1], self.max_plies, kinds[0], kinds[1])

    def collect(self, target_decisions: int, seed: int, log=sys.stderr) -> tuple[list[RolloutEpisode], dict]:
        rng = random.Random(seed)
        next_seed = seed * 100_000
        games: list[env.Game] = []
        finished: list[RolloutEpisode] = []
        records: list[env.GameRecord] = []
        decisions = 0
        started = time.time()
        stop_starting = False
        while True:
            while not stop_starting and len(games) < self.games_in_flight:
                games.append(self.new_game(next_seed, rng))
                next_seed += 1
            if not games:
                break
            # 1. deliver observations, batching the neural players' recurrent updates
            neural_to_observe = []
            for game in games:
                if game.need_delivery:
                    game.deliver()
                    for player in game.players:
                        if player.neural:
                            neural_to_observe.append(player)
            if neural_to_observe:
                self.run_observe(neural_to_observe)
            # 2. decide for the side to move
            neural_to_score = []
            for game in games:
                player = game.players[game.side_to_move]
                if player.neural:
                    neural_to_score.append(player)
            choices = self.run_score(neural_to_score, rng) if neural_to_score else {}
            for game in games:
                side = game.side_to_move
                player = game.players[side]
                if player.neural:
                    uci, index, log_prob = choices.get(id(player), (None, -1, 0.0))
                    if uci is not None and player.learner:
                        cands = player.pending_candidates
                        player.transitions.append(env.Transition(
                            event=len(player.observations) - 1, candidates=cands, action_index=index,
                            log_prob=log_prob, value=player.last_value,
                            danger=env.danger_labels(game, cands), board=game.state.board.board_string()))
                        decisions += 1
                else:
                    uci = player.decide(game.rng)
                if uci is None:
                    game.forfeit(side, "No legal moves")
                else:
                    game.push(uci)
            # 3. retire finished games
            still = []
            for game in games:
                if game.done:
                    records.append(game.record())
                    for side, player in enumerate(game.players):
                        if player.neural and player.learner:
                            finished.append(self.finalize(player, game, side))
                else:
                    still.append(game)
            games = still
            if decisions >= target_decisions:
                stop_starting = True
            if len(records) and len(records) % 50 == 0 and log:
                rate = decisions / max(time.time() - started, 1e-6)
                print(f"  rollout: {len(records)} games, {decisions} decisions, {rate:.1f} dec/s", file=log)
        elapsed = time.time() - started
        stats = summarize(records, decisions, elapsed)
        return finished, stats

    def finalize(self, player: env.NeuralPlayer, game: env.Game, side: int) -> RolloutEpisode:
        result = game.outcome[0]
        ret = labels.terminal_return(result, side)
        K = len(player.transitions)
        reward = np.zeros(K, dtype=np.float32)
        terminated = np.zeros(K, dtype=bool)
        if K:
            reward[-1] = ret
            terminated[-1] = True
        actor = histories.ActorRecord(
            side, list(player.observations), list(player.phases), list(player.plies),
            [t.event for t in player.transitions], [t.candidates[t.action_index] for t in player.transitions],
            [t.candidates for t in player.transitions], [-1] * K, [0] * K)
        targets = histories.TargetRecord(
            [t.board for t in player.transitions], [t.danger for t in player.transitions],
            [t.candidates[t.action_index] for t in player.transitions], ret,
            [True] * K, [True] * K, [True] * K, [True] * K)
        opponent = game.kinds[side ^ 1]
        metadata = histories.EpisodeMetadata(
            game_id=f"sim{game.seed}", player_id="learner", opponent_id=opponent, played_version=None,
            opponent_version=None, submission_id=None, result=result, reason=game.outcome[1],
            termination="normal", rules_fingerprint="simulator")
        return RolloutEpisode(
            histories.PlayerEpisode(actor, targets, metadata),
            np.array([t.action_index for t in player.transitions], dtype=np.int64),
            np.array([t.log_prob for t in player.transitions], dtype=np.float32),
            np.array([t.value for t in player.transitions], dtype=np.float32),
            reward, terminated, np.zeros(K, dtype=bool), 0.0, opponent, game.seed)


def summarize(records: list[env.GameRecord], decisions: int, elapsed: float) -> dict:
    by_opponent: dict[str, dict] = {}
    for record in records:
        learner_side = 0 if record.white_kind == "learner" else 1
        opponent = record.black_kind if learner_side == 0 else record.white_kind
        entry = by_opponent.setdefault(opponent, {"games": 0, "wins": 0, "draws": 0, "losses": 0})
        entry["games"] += 1
        score = labels.terminal_return(record.result, learner_side)
        entry["wins" if score > 0 else "losses" if score < 0 else "draws"] += 1
    forfeits = {}
    for record in records:
        if record.reason.startswith("Illegal move") or record.reason == "No legal moves":
            loser = "white" if record.result == "0-1" else "black"
            kind = record.white_kind if loser == "white" else record.black_kind
            forfeits[f"{kind}:{record.reason.split(':')[0]}"] = forfeits.get(f"{kind}:{record.reason.split(':')[0]}", 0) + 1
    total = sum(e["games"] for e in by_opponent.values())
    wins = sum(e["wins"] for e in by_opponent.values())
    draws = sum(e["draws"] for e in by_opponent.values())
    return {"games": total, "decisions": decisions, "elapsed": elapsed,
            "decisions_per_second": decisions / max(elapsed, 1e-6),
            "score_rate": (wins + 0.5 * draws) / max(total, 1), "by_opponent": by_opponent,
            "mean_plies": float(np.mean([r.plies for r in records])) if records else 0.0,
            "forfeits": forfeits, "training_mode": env.TRAINING_MODE}


def compute_gae(rollout: RolloutEpisode, gamma: float, lam: float) -> tuple[np.ndarray, np.ndarray]:
    """Advantages and returns over the learner's same-player transitions."""
    K = len(rollout.reward)
    advantages = np.zeros(K, dtype=np.float32)
    last = 0.0
    for k in reversed(range(K)):
        if rollout.terminated[k]:
            next_value = 0.0
            last = 0.0
        elif k == K - 1:
            next_value = rollout.bootstrap_value if rollout.rollout_cut[k] else 0.0
        else:
            next_value = rollout.old_value[k + 1]
        delta = rollout.reward[k] + gamma * next_value - rollout.old_value[k]
        last = delta + gamma * lam * last * (0.0 if rollout.terminated[k] else 1.0)
        advantages[k] = last
    returns = advantages + rollout.old_value
    return advantages, returns
