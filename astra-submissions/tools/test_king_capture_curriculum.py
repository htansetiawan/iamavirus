"""Curriculum selection, source alignment and temporal-input contracts."""
import copy
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("capture_subject", Path(__file__).with_name("king_capture_curriculum.py"))
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


def fixture():
    board = list("-" * 64)
    board[4], board[12], board[60] = "K", "p", "k"
    view = board.copy()
    view[60] = "?"
    actor = dict(side=0, observations=["".join(view)], phases=[0], plies=[0],
        decision_event_indices=[0], own_actions=["e1e2"],
        legal_actions=[["e1d1", "e1e2"]], inferred_en_passant=[-1], castling_rights=[0])
    targets = dict(boards=["".join(board)], king_loss_by_action=[[0, 0]],
                   policy_valid=[True], danger_valid=[True])
    metadata = dict(game_id="game0000", source_hash="a" * 64, split="train", candidate_mismatches=[])
    return dict(actor=actor, targets=targets, metadata=metadata)


class CaptureCurriculumTests(unittest.TestCase):
    def test_safe_and_hidden_covered_captures_are_both_preserved(self):
        episode = fixture()
        safe = list(subject.records(episode))
        self.assertEqual(len(safe), 1)
        self.assertFalse(safe[0]["targets"]["king_loss"])
        self.assertFalse(safe[0]["targets"]["all_cover_hidden"])
        # Hidden rook on e8 covers the e2 capture from behind fog.
        board = list(episode["targets"]["boards"][0])
        board[60], board[56] = "r", "k"
        episode["targets"]["boards"][0] = "".join(board)
        episode["targets"]["king_loss_by_action"][0][1] = 1
        fatal = list(subject.records(episode))
        self.assertEqual(safe[0]["inputs"], fatal[0]["inputs"])
        self.assertTrue(fatal[0]["targets"]["king_loss"])
        self.assertTrue(fatal[0]["targets"]["all_cover_hidden"])
        self.assertTrue(fatal[0]["targets"]["avoidable"])
        self.assertEqual(fatal[0]["targets"]["cover"][0]["piece"], "R")

    def test_chosen_action_metadata_and_validity_are_not_inputs(self):
        episode = fixture()
        original = list(subject.records(episode))[0]
        self.assertFalse(set(original["inputs"]) & {"history", "prefix_fingerprint", "source_hash", "sample_id"})
        changed = copy.deepcopy(episode)
        changed["actor"]["own_actions"][0] = "e1d1"
        changed["targets"]["policy_valid"][0] = False
        changed["metadata"].update(game_id="other000", source_hash="b" * 64, split="test", result="0-1")
        result = list(subject.records(changed))[0]
        self.assertEqual(original["inputs"], result["inputs"])
        self.assertTrue(original["targets"]["played"])
        self.assertFalse(result["targets"]["played"])
        self.assertFalse(result["targets"]["choice_valid"])

    def test_future_view_does_not_change_current_inputs(self):
        episode = fixture()
        original = list(subject.records(episode))[0]
        changed = copy.deepcopy(episode)
        changed["actor"]["observations"].append("?" * 64)
        changed["actor"]["phases"].append(1)
        changed["actor"]["plies"].append(1)
        self.assertEqual(original["inputs"], list(subject.records(changed))[0]["inputs"])

    def test_enemy_king_capture_and_nonking_move_are_excluded(self):
        episode = fixture()
        prefix = next(subject.actors.actor_decisions(episode["actor"]))
        view = list(subject.actors.unpack_view(prefix["observation"]))
        view[12] = "k"
        prefix["observation"] = subject.actors.pack_view("".join(view))
        self.assertIsNone(subject.candidate_inputs(prefix, "e1e2"))
        self.assertIsNone(subject.candidate_inputs(prefix, "e1d1"))

    def test_wrong_danger_alignment_or_source_is_rejected(self):
        for mutation in ("short", "wrong_risk", "source", "blocked"):
            episode = fixture()
            if mutation == "short":
                episode["targets"]["king_loss_by_action"][0].pop()
            elif mutation == "wrong_risk":
                episode["targets"]["king_loss_by_action"][0][1] = 1
            elif mutation == "source":
                episode["metadata"]["source_hash"] = "unbound"
            else:
                episode["metadata"]["candidate_mismatches"] = [dict(ply=0)]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                list(subject.records(episode))


if __name__ == "__main__":
    unittest.main()
