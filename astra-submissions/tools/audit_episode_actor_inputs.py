"""Audit causal policy-input encoding on the already reviewed 30-game cohort.

Reuses the existing episode/feature APIs and rules validator. Independent
raw-square memory checks and label interventions extend existing history tests
to these replay inputs. No model, raw export, split or training is changed.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import audit_training_artifacts as shared_audit
from learning import _native, dataset, features, histories, ingest

NAME = "episode-actor-inputs-20261111"
OUT = ROOT / "astra-submissions/analysis" / NAME
PRIVATE = ROOT / "data/astra-spool" / NAME
COHORT = ROOT / "data/astra-spool/daily-own-cohort-20261111"
PRIOR = ROOT / "astra-submissions/analysis/daily-own-cohort-20261111"
VALIDATOR = ROOT / "astra-submissions/experiments/last-only-pilot-20261110/build/native-validator.so"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def policy_arrays_equal(first, second):
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])
    assert len(first[2]) == len(second[2])
    for a, b in zip(first[2], second[2], strict=True):
        for key in ("event", "count", "from", "to", "promo"):
            assert np.array_equal(a[key], b[key]), key


def check_encoding(actor, planes, scalars):
    """Decode documented channels using a raw-square history accumulator."""
    actions = dict(zip(actor.decision_event_indices, actor.own_actions, strict=True))
    eps = dict(zip(actor.decision_event_indices, actor.inferred_en_passant, strict=True))
    rights = dict(zip(actor.decision_event_indices, actor.castling_rights, strict=True))
    last_content, last_ply = [None] * 64, [-1] * 64
    previous_move = None
    king_home = 4 if actor.side == 0 else 60
    rook_homes = (0, 7) if actor.side == 0 else (56, 63)
    own_king, own_rook = ("K", "R") if actor.side == 0 else ("k", "r")
    king_side = queen_side = True
    counts = Counter()
    for e, (view, phase, ply) in enumerate(zip(actor.observations, actor.phases, actor.plies, strict=True)):
        assert ply == e
        assert phase == (0 if e == 0 else 1 if (e - 1) % 2 == actor.side else 2)
        if view[king_home] != own_king:
            king_side = queen_side = False
        if view[rook_homes[0]] != own_rook:
            queen_side = False
        if view[rook_homes[1]] != own_rook:
            king_side = False
        expected_rights = (1 << rook_homes[0] if queen_side else 0) | (1 << rook_homes[1] if king_side else 0)
        if e in rights:
            assert rights[e] == expected_rights
        p = planes[e].reshape(32, 64)
        assert np.all(p[:14].sum(axis=0) == 1)
        for raw, symbol in enumerate(view):
            square = raw if actor.side == 0 else raw ^ 56
            if symbol == "?":
                current_class = 12
            elif symbol == "-":
                current_class = 13
            else:
                current_class = "PNBRQK".index(symbol.upper()) + (0 if symbol.isupper() == (actor.side == 0) else 6)
            assert p[current_class, square] == 1
            if symbol != "?":
                last_content[raw], last_ply[raw] = symbol, ply
            memory = p[14:27, square]
            if last_content[raw] is None:
                assert memory.sum() == 0 and p[27, square] == 0 and p[28, square] == 1
            else:
                content = last_content[raw]
                label = 12 if content == "-" else "PNBRQK".index(content.upper()) + (0 if content.isupper() == (actor.side == 0) else 6)
                assert memory.sum() == 1 and memory[label] == 1 and p[27, square] == 1
                assert p[28, square] == np.float32(min(ply - last_ply[raw], 100) / 100)
            for channel, raw_square in ((29, previous_move[0] if previous_move else -1),
                                        (30, previous_move[1] if previous_move else -1),
                                        (31, eps.get(e, -1))):
                expected = float(raw == raw_square)
                assert p[channel, square] == expected
            counts["checked_square_events"] += 1
        np.testing.assert_array_equal(scalars[e], np.array([
            actor.side, int(ply % 2 == actor.side), int(king_side), int(queen_side),
            int(phase == 0), int(phase == 1), int(phase == 2), min(ply, 1000) / 1000,
        ], dtype=np.float32))
        if e in actions:
            move = actions[e]
            f = 8 * (int(move[1]) - 1) + ord(move[0]) - ord("a")
            t = 8 * (int(move[3]) - 1) + ord(move[2]) - ord("a")
            previous_move = (f, t)
            if f == king_home and view[f] == own_king:
                king_side = queen_side = False
            if f == rook_homes[0]:
                queen_side = False
            if f == rook_homes[1]:
                king_side = False
    return counts


def main():
    OUT.mkdir(exist_ok=False)
    PRIVATE.mkdir(exist_ok=False)
    prior = read(PRIOR / "plan.json")
    paths = [Path(__file__), Path(shared_audit.__file__), VALIDATOR, PRIOR / "plan.json", PRIOR / "result.json", PRIOR / "review.json"]
    paths.extend(ROOT / "learning" / (name + ".py") for name in ("features", "histories", "dataset", "ingest", "rules", "_native", "labels", "action_codec"))
    for game in prior["game_ids"]:
        path = COHORT / "games" / game / "replay.json"
        assert sha(path) == prior["dependencies"][str(path.relative_to(ROOT))]
        paths.append(path)
    assert len(prior["game_ids"]) == 30
    plan = {"at": now(), "games": prior["game_ids"], "core": 6, "wall_cap_seconds": 180,
            "source_sha256": {str(p): sha(p) for p in paths},
            "antecedents": "Existing test_histories information-isolation/event-rhythm tests and feature parity; 389's exact all-30 cohort. This is their bounded application to real replay data, not a new privacy algorithm.",
            "scope": "Actor encoding, timing, candidate/source alignment and explicit label/metadata interventions; no logits, model fit, raw export, split, native build, game or strength claim."}
    save(OUT / "plan.json", plan)
    assert _native._library is None
    _native.ensure_built = lambda verbose=True: VALIDATOR
    shared_audit.NAME = NAME
    started = time.monotonic()
    def timeout(*_):
        raise TimeoutError("original 180-second actor-input audit cap reached")
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(plan["wall_cap_seconds"])
    state = {"at": now(), "status": "running", "plan_sha256": sha(OUT / "plan.json")}
    save(OUT / "execution.json", state)
    rows, totals = [], Counter()
    try:
        with shared_audit.lease():
            for game in prior["game_ids"]:
                replay = read(COHORT / "games" / game / "replay.json")
                states, problems = ingest.validate_replay(replay)
                assert not problems
                for side in (0, 1):
                    ep = histories.build_episode(replay, states, side, ingest.RULES_FINGERPRINT)
                    assert not ep.metadata.candidate_mismatches
                    assert ep.metadata.termination == histories.TERMINATION_NORMAL
                    actor = ep.actor
                    key = "white" if side == 0 else "black"
                    assert actor.observations == [f[key] for f in replay["frames"][:-1]]
                    original = dataset.episode_tensors(ep)
                    counts = check_encoding(actor, original[0], original[1])
                    for i, event in enumerate(actor.decision_event_indices):
                        assert actor.own_actions[i] == replay["frames"][event + 1]["move"]
                        assert ep.targets.boards[i] == replay["frames"][event]["board"]
                        assert sorted(actor.legal_actions[i]) == sorted(states[event].board.legal_moves())
                    altered = deepcopy(ep)
                    altered.targets.boards = ["-" * 64] * ep.num_decisions
                    altered.targets.king_loss_by_action = [[1 - x for x in r] for r in ep.targets.king_loss_by_action]
                    altered.targets.terminal_return = ep.targets.terminal_return + 1
                    altered.targets.policy_valid = [not x for x in ep.targets.policy_valid]
                    altered.targets.value_valid = [not x for x in ep.targets.value_valid]
                    altered.metadata.player_id = "intervened-player"
                    altered.metadata.opponent_id = "intervened-opponent"
                    changed = dataset.episode_tensors(altered)
                    policy_arrays_equal(original, changed)
                    assert all(a["return"] != b["return"] for a, b in zip(original[2], changed[2], strict=True))
                    own = dict(zip(actor.decision_event_indices, actor.own_actions, strict=True))
                    cut = len(actor.observations) // 2
                    prefix = features.replay_events(side, actor.observations[:cut], actor.phases[:cut], actor.plies[:cut], own)
                    assert np.array_equal(prefix[0], original[0][:cut]) and np.array_equal(prefix[1], original[1][:cut])
                    # Intervene on a current action, checking the feature event
                    # before that action and a following real observation.
                    action_control = False
                    for i, event in enumerate(actor.decision_event_indices):
                        options = [m for m in actor.legal_actions[i] if m[:4] != actor.own_actions[i][:4]]
                        if not options or event + 1 >= len(actor.observations):
                            continue
                        alternative = dict(own)
                        alternative[event] = options[0]
                        p, s = features.replay_events(side, actor.observations, actor.phases, actor.plies, alternative)
                        assert np.array_equal(p[:event + 1], original[0][:event + 1])
                        assert np.array_equal(s[:event + 1], original[1][:event + 1])
                        assert not np.array_equal(p[event + 1, 29:31], original[0][event + 1, 29:31])
                        action_control = True
                        break
                    assert action_control
                    row = {"game": game, "side": side, "events": len(actor.observations),
                           "decisions": ep.num_decisions, **counts,
                           "feature_sha256": hashlib.sha256(original[0].tobytes() + original[1].tobytes()).hexdigest(),
                           "label_intervention_passed": True, "future_truncation_passed": True,
                           "current_action_timing_control_passed": action_control}
                    rows.append(row)
                    totals.update({"episodes": 1, "events": row["events"], "decisions": row["decisions"], **counts})
        for path, digest in plan["source_sha256"].items():
            assert sha(Path(path)) == digest
        assert "torch" not in sys.modules
        save(PRIVATE / "episode-receipts.json", rows)
        result = {"at": now(), "status": "complete", "plan_sha256": sha(OUT / "plan.json"),
                  "games": 30, "counts": dict(totals), "interventions_per_kind": len(rows),
                  "receipt_sha256": sha(PRIVATE / "episode-receipts.json"),
                  "scope": plan["scope"],
                  "limitations": ["Only this exposed 30-game cohort; not every historical or future episode.",
                                  "Interventions test the data interface; they are not alternate valid full-game histories or a complete information-set proof.",
                                  "No C++ feature-parity rerun or trained-model/logit evaluation.",
                                  "The episode-policy pipeline is retired from deployed v38; no current v38 strength result."]}
        save(OUT / "result.json", result)
        state.update(status="complete", result_sha256=sha(OUT / "result.json"))
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        state.update(status="failed", error=repr(exc))
        raise
    finally:
        signal.alarm(0)
        state.update(ended_at=now(), seconds=time.monotonic() - started)
        shared_audit.update(OUT / "execution.json", state)


if __name__ == "__main__":
    main()
