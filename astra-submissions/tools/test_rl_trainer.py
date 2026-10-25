"""Regression tests for Fable's batched trainer. CPU only; no training jobs."""
import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning.batch_env import BatchEnv
from learning.model import FogPolicy, masked_log_softmax
from learning.critic import Critic
from learning.rl_train import Member, Rollout, critic_bootstraps, critic_values, gae, update

torch.set_num_threads(1)


def transition(slot=0, reward=0.0, done=False):
    return {"game": slot, "reward": reward, "done": done}


def test_cutoff_uses_successor_value_and_propagates_it_backwards():
    a, r = gae([transition(), transition()], np.array([0.1, 0.2]), 1.0, 0.95,
               bootstrap_values={0: 0.8})
    np.testing.assert_allclose(a, [0.67, 0.6])
    np.testing.assert_allclose(r, [0.77, 0.8])


def test_interleaved_slots_and_reused_terminal_slot_are_isolated():
    trans = [transition(0, 1, True), transition(1), transition(0), transition(1, -1, True)]
    a, r = gae(trans, np.array([0.2, 0.1, 0.3, 0.4]), 1.0, 1.0,
               bootstrap_values={0: 0.8})
    np.testing.assert_allclose(a, [0.8, -1.1, 0.5, -1.4])
    np.testing.assert_allclose(r, [1.0, -1.0, 0.8, -1.0])


@pytest.mark.parametrize("reward", [-1.0, 0.0, 1.0])
def test_terminal_never_bootstraps(reward):
    _, r = gae([transition(0, reward, True)], np.array([0.2]), 1.0, 0.95,
               bootstrap_values={0: 999.0})
    np.testing.assert_allclose(r, [reward], atol=1e-7)


def test_missing_cutoff_value_is_an_error():
    with pytest.raises(ValueError, match="bootstrap"):
        gae([transition()], np.array([0.2]), 1.0, 0.95)


class FixedRandom:
    """Choose learner White, and the first positive-weight league member."""
    def randrange(self, n):
        return 0

    def choices(self, population, weights):
        return [next(i for i, w in zip(population, weights) if w > 0)]


class ScriptedEnv:
    """Two learner turns separated by replies; optionally terminal on ply 1/2."""
    n = 1

    def __init__(self, terminal_ply=None, status=1):
        self.terminal_ply, self.terminal_status = terminal_ply, status
        self.ply, self.episode = 0, 0
        self.actions = []
        self.events_taken = []

    def side_to_move(self, i):
        return self.ply % 2

    def take_events(self, i, side):
        self.events_taken.append((self.episode, self.ply, side))
        return np.zeros((1, 32, 8, 8), np.float32), np.zeros((1, 8), np.float32)

    def candidates(self, i):
        return np.array([8, 9], np.int32), np.array([16, 17], np.int32), np.zeros(2, np.int32)

    def board(self, i):
        return f"episode={self.episode},ply={self.ply}"

    def step_all(self, actions):
        if actions[0] >= 0:
            self.actions.append((self.episode, self.ply, int(actions[0])))
            self.ply += 1
        terminal = self.ply == self.terminal_ply
        return np.array([self.terminal_status if terminal else 0], np.int32)

    def reset(self, i):
        self.ply = 0
        self.episode += 1


def model(hidden=16, channels=4):
    return FogPolicy(channels=channels, blocks=0, hidden=hidden, cand_width=8).eval()


def collector(env, learner=None, reference=None, league=None, group_weights=None):
    return Rollout(env, learner or model(), reference or model(),
                   league or [Member("opponent", model(), 1.0)], torch.device("cpu"), FixedRandom(),
                   group_weights)


def test_cutoff_finishes_reply_without_consuming_next_learner_observation():
    env = ScriptedEnv()
    roll = collector(env)
    trans, results = roll.collect(1)
    assert len(trans) == 1 and not results and not trans[0]["done"]
    assert roll.last_decision_counts == {"default:opponent": 1}
    assert env.ply == 2
    assert roll.bootstrap_states == {0: {"board": "episode=0,ply=2", "side": 0}}
    assert env.events_taken == [(0, 0, 0), (0, 1, 1)]
    more, _ = roll.collect(1)
    assert more[0]["board"] == "episode=0,ply=2"
    assert roll.bootstrap_states[0]["board"] == "episode=0,ply=4"


def test_rollout_logs_actual_learner_decision_exposure_by_group_and_member():
    league = [Member("target-bot", model(), 1.0, "targets")]
    roll = collector(ScriptedEnv(), league=league, group_weights={"targets": 1.0})
    trans, _ = roll.collect(1)
    assert len(trans) == 1
    assert roll.last_decision_counts == {"targets:target-bot": 1}


@pytest.mark.parametrize("terminal_ply,status,reward", [(1, 2, -1), (2, 1, 1), (2, 3, 0)])
def test_boundary_terminal_reward_attached_once_before_reset(terminal_ply, status, reward):
    env = ScriptedEnv(terminal_ply, status)
    roll = collector(env)
    trans, results = roll.collect(1)
    assert len(trans) == 1 and trans[0]["done"] and trans[0]["reward"] == reward
    assert results == [(0, (reward + 1) / 2)]
    assert roll.bootstrap_states == {}
    assert env.episode == 1 and env.ply == 0
    assert len(env.actions) == terminal_ply  # No action in the reset game.


def test_models_with_different_memories_and_new_snapshot_can_share_rollout():
    env = ScriptedEnv(terminal_ply=2)
    league = [Member("small", model(8, 2), 1.0)]
    roll = collector(env, model(32, 6), model(16, 4), league)
    trans, _ = roll.collect(3)
    assert len(trans) == 3 and all(t["h"].shape == (32,) for t in trans)
    # Newly added snapshot can have a different memory size again.
    league[0].weight = 0.0
    league.append(Member("new", model(48, 8), 1.0))
    roll._assign(0)
    trans, results = roll.collect(1)
    assert len(trans) == 1 and results[0][0] == 1


def test_real_simulator_mixed_widths_and_logged_policy_agree():
    torch.manual_seed(7)
    learner = model(32, 6)
    roll = Rollout(BatchEnv(4, max_plies=12), learner, model(16, 4),
                   [Member("small", model(8, 2), 1.0), Member("wide", model(48, 8), 1.0)],
                   torch.device("cpu"), random.Random(11))
    trans, results = roll.collect(35, temperature=0.7)
    assert len(trans) >= 35 and results
    for slot, state in roll.bootstrap_states.items():
        assert roll.env.side_to_move(slot) == state["side"]
        assert roll.env.board(slot) == state["board"]
    with torch.no_grad():
        for t in trans:
            h = t["h"].unsqueeze(0)
            for planes, scalars in zip(*t["events"]):
                h, spatial, _, _ = learner.observe(torch.from_numpy(planes).unsqueeze(0),
                                                   torch.from_numpy(scalars).unsqueeze(0), h)
            candidates = [torch.from_numpy(c.astype(np.int64)).unsqueeze(0) for c in t["cand"]]
            logits, _ = learner.score(h, spatial, *candidates)
            logp = masked_log_softmax(logits / 0.7, torch.ones_like(logits, dtype=torch.bool))
            assert float(logp[0, t["action"]]) == pytest.approx(t["old_logp"], abs=1e-5)


def test_ppo_update_recomputes_behavior_temperature_and_has_finite_gradients():
    torch.manual_seed(12)
    learner = model(32, 6)
    with torch.no_grad():
        learner.policy_out.weight.mul_(20)
    roll = collector(BatchEnv(3, max_plies=30), learner, model(16, 4),
                     [Member("small", model(8, 2), 1.0)])
    trans, _ = roll.collect(12, temperature=0.35)
    critic = Critic(channels=4, blocks=0)
    device = torch.device("cpu")
    values, xs = critic_values(critic, trans, device)
    bootstraps = critic_bootstraps(critic, roll.bootstrap_states, device)
    adv, ret = gae(trans, values, 1.0, 0.95, bootstraps)
    # Zero actor LR isolates recomputation of the behavior distribution across
    # multiple minibatches. The critic still performs a real optimizer update.
    opt_a = torch.optim.Adam(learner.parameters(), lr=0.0)
    opt_c = torch.optim.Adam(critic.parameters(), lr=1e-4)
    cfg = {"minibatch": 4, "epochs": 1, "clip": 0.2, "kl_ref_coef": 0.05,
           "entropy_coef": 0.003, "grad_clip": 1.0, "temperature": 1.0}
    stats = update(learner, critic, opt_a, opt_c, trans, adv, ret, xs, cfg, device)
    assert abs(stats["approx_kl"]) < 1e-4
    assert stats["clip_frac"] == 0.0
    assert all(np.isfinite(v) for v in stats.values())
    assert all(torch.isfinite(p.grad).all() for p in learner.parameters() if p.grad is not None)


def test_split_and_unsplit_returns_match_with_exact_cutoff_value():
    trans = [transition(), transition(), transition(0, 1, True)]
    values = np.array([0.2, 0.5, 0.7])
    _, full = gae(trans, values, 1.0, 1.0)
    # The continuation's exact return is 1, not the pre-cutoff value 0.5.
    _, prefix = gae(trans[:2], values[:2], 1.0, 1.0, bootstrap_values={0: 1.0})
    np.testing.assert_allclose(prefix, full[:2])
