"""PPO accounting: the stored action and log-probability refer to the same
masked behaviour distribution the trainer recomputes, and same-player rewards,
terminal flags and bootstrap masks are right whether the game ends on our move
or the opponent's."""
import random

import numpy as np
import torch

from learning import env, rollouts
from learning.model import FogPolicy, masked_log_softmax
from learning.train_ppo import ppo_batch


def _collect(model, decisions=40, seed=5):
    device = torch.device("cpu")
    league = rollouts.League(recent=[], older=[], fixed=["uniform-random"], recent_share=0, older_share=0, fixed_share=1)
    collector = rollouts.Collector(model, {}, device, league, games_in_flight=4, max_plies=60)
    episodes, stats = collector.collect(decisions, seed)
    return [e for e in episodes if len(e.action_index) > 0], stats


def test_logged_log_probs_match_recomputed_masked_policy():
    torch.manual_seed(0)
    model = FogPolicy().eval()
    episodes, _ = _collect(model)
    assert episodes
    rng = random.Random(0)
    batch, extras = ppo_batch(episodes[:3], 64, rng, 1.0, 0.95)
    tensors = {k: torch.from_numpy(np.ascontiguousarray(v)) for k, v in batch.__dict__.items()}
    with torch.no_grad():
        hidden = torch.zeros(tensors["planes"].shape[0], 256)
        from learning.pretrain import run_sequence
        hiddens, spatials, _, _ = run_sequence(model, tensors["planes"], tensors["scalars"], tensors["window_lengths"], hidden)
        seq, step = tensors["decision_seq"], tensors["decision_step"]
        logits, _ = model.score(hiddens[seq, step], spatials[seq, step], tensors["cand_from"], tensors["cand_to"], tensors["cand_promo"])
        log_probs = masked_log_softmax(logits, tensors["cand_mask"])
        recomputed = log_probs.gather(1, torch.from_numpy(extras["action"]).unsqueeze(1)).squeeze(1).numpy()
    assert np.allclose(recomputed, extras["old_logp"], atol=1e-4), (recomputed, extras["old_logp"])
    # Every logged action is inside the candidate mask.
    counts = batch.cand_count
    assert np.all(extras["action"] < counts)


def test_same_player_rewards_and_terminal_flags():
    torch.manual_seed(1)
    model = FogPolicy().eval()
    episodes, stats = _collect(model, decisions=120, seed=9)
    assert stats["games"] > 0
    for e in episodes:
        K = len(e.action_index)
        # Only the final transition carries the reward and the terminal flag.
        assert e.terminated[-1] and not e.terminated[:-1].any()
        assert e.reward[:-1].sum() == 0.0
        assert e.reward[-1] in (-1.0, 0.0, 1.0)
        assert e.reward[-1] == e.episode.targets.terminal_return
        # The history has one more delivered view than decisions when the game
        # ended on the opponent's move, and equal counts when it ended on ours
        # (no terminal view is delivered either way).
        events = len(e.episode.actor.observations)
        last_decision = e.episode.actor.decision_event_indices[-1]
        assert events - 1 in (last_decision, last_decision + 1)
        adv, ret = rollouts.compute_gae(e, 1.0, 0.95)
        assert np.isclose(ret[-1], e.reward[-1])  # no bootstrap past a terminal
        assert not e.rollout_cut.any()


def test_truncated_rollout_bootstraps_from_value():
    e = rollouts.RolloutEpisode(None, np.zeros(2, dtype=np.int64), np.zeros(2, dtype=np.float32),
                                np.array([0.2, 0.4], dtype=np.float32), np.zeros(2, dtype=np.float32),
                                np.zeros(2, dtype=bool), np.array([False, True]), bootstrap_value=0.5,
                                opponent="x", seed=0)
    adv, ret = rollouts.compute_gae(e, 1.0, 1.0)
    # Last transition: delta = 0 + 0.5 - 0.4 = 0.1; first: 0 + 0.4 - 0.2 + 0.1 = 0.3
    assert np.allclose(adv, [0.3, 0.1])
    assert np.allclose(ret, [0.5, 0.5])
