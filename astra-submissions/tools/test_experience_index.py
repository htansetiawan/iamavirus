"""Codec, information boundary, duplicate-split and retrieval contract tests."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("experience_index", Path(__file__).with_name("experience_index.py"))
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)


def actor():
    view = list("?" * 64)
    view[4], view[15], view[23], view[31] = "K", "P", "-", "-"
    first = "".join(view)
    view[15], view[23] = "-", "P"
    second = "".join(view)
    return dict(side=0, observations=[first, second, second], phases=[0, 1, 2], plies=[0, 1, 2],
        decision_event_indices=[0, 2], own_actions=["h2h3", "h3h4"],
        legal_actions=[["h2h3", "h2h4"], ["h3h4", "e1d1"]],
        inferred_en_passant=[-1, -1], castling_rights=[0, 0])


def fixture(root, splits=("train", "validation", "test"), duplicate=False):
    shards, accepted = {}, []
    for number, split in enumerate(splits):
        game = f"game{number:04d}"
        path = root / (split + ".jsonl.gz")
        episode = dict(actor=actor(), targets={"boards": "PRIVILEGED DATA MUST NOT BE READ"},
            metadata=dict(game_id=game, source_hash="source", split=split, player_id="test",
                          opponent_id="opponent", candidate_mismatches=[]))
        with gzip.open(path, "wt") as handle:
            handle.write(json.dumps(episode) + "\n")
        shards[split] = str(path)
        accepted.append(dict(id=game, moves_sha256="same" if duplicate else game))
    manifest = root / "source.json"
    manifest.write_text(json.dumps(dict(shards=shards)))
    acceptance = root / "accepted.jsonl"
    acceptance.write_text("".join(json.dumps(row) + "\n" for row in accepted))
    return manifest, acceptance


class ExperienceTests(unittest.TestCase):
    def test_lossless_symbols_and_unknown(self):
        rng = random.Random(42)
        for _ in range(500):
            view = "".join(rng.choice(index.SYMBOLS) for _ in range(64))
            self.assertEqual(index.unpack_view(index.pack_view(view)), view)
            self.assertEqual(len(index.pack_view(view)), 32)
        self.assertNotEqual(index.pack_view("-" * 64), index.pack_view("?" * 64))
        with self.assertRaises(ValueError):
            index.unpack_view(bytes([255]) * 32)

    def test_current_action_and_future_do_not_enter_prefix(self):
        control = actor()
        changed = copy.deepcopy(control)
        changed["own_actions"][0] = "h2h4"
        before, after = list(index.actor_decisions(control)), list(index.actor_decisions(changed))
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1]["history"], after[1]["history"])
        changed = copy.deepcopy(control)
        changed["observations"][2] = changed["observations"][2].replace("?", "-", 1)
        self.assertEqual(before[0], list(index.actor_decisions(changed))[0])

    def test_last_seen_is_not_overwritten_by_fog(self):
        a = actor()
        view = list(a["observations"][0]); view[40] = "r"
        a["observations"][0] = "".join(view)
        rows = list(index.actor_decisions(a))
        self.assertEqual(index.unpack_view(rows[1]["observation"])[40], "?")
        self.assertEqual(index.unpack_view(rows[1]["memory"])[40], "r")
        self.assertEqual(rows[1]["ages"][40], 2)
        self.assertEqual(rows[1]["ages"][41], 255)
        # A later visible empty square clears the memory rather than retaining a rook.
        view[40] = "-"
        a["observations"][2] = "".join(view)
        self.assertEqual(index.unpack_view(list(index.actor_decisions(a))[1]["memory"])[40], "-")

    def test_move_codec_no_promotion_collisions(self):
        self.assertEqual(len({index.pack_move("e7e8" + s) for s in ("", "q", "r", "b", "n")}), 5)
        self.assertEqual(index.pack_move("a1b1"), b"@\x00")
        for bad in ("i1a2", "a0a2", "e7e8k"):
            with self.assertRaises(ValueError): index.pack_move(bad)

    def test_index_train_only_budget_and_duplicate_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, accepted = fixture(root)
            output = root / "index"
            index.build(manifest, accepted, output)
            db = output / "actors.sqlite"
            answer = index.query(db, actor()["observations"][0], 0, top=1, budget=1)
            self.assertEqual(answer["candidates_examined"], 1)
            self.assertTrue(answer["truncated"])
            self.assertEqual(answer["matches"][0]["game"], "game0000")
            self.assertEqual(index.query(db, actor()["observations"][0], 0,
                exclude_game="game0000")["matches"], [])
            prefix = next(index.actor_decisions(actor()))["history"]
            exact = index.query(db, actor()["observations"][0], 0, history=prefix)
            self.assertEqual(len(exact["matches"]), 1)
            connection = sqlite3.connect(db)
            columns = {r[1] for r in connection.execute("PRAGMA table_info(decisions)")}
            self.assertFalse(columns & {"board", "result", "target", "opponent_move", "own_action"})
            connection.close()

    def test_duplicate_trajectory_split_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, accepted = fixture(root, duplicate=True)
            with self.assertRaisesRegex(ValueError, "crosses dataset split"):
                index.build(manifest, accepted, root / "index")
            self.assertFalse((root / "index" / "manifest.json").exists())

    def test_query_empty_exact_budget_and_top_equal_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, accepted = fixture(root, splits=("train",))
            index.build(manifest, accepted, root / "index")
            database = root / "index/actors.sqlite"
            view = actor()["observations"][0]
            exact = index.query(database, view, 0, top=2, budget=2)
            self.assertEqual(exact["candidates_examined"], 2)
            self.assertFalse(exact["truncated"])
            self.assertEqual([r["ply"] for r in exact["matches"]], [0, 2])
            over = index.query(database, view, 0, top=1, budget=1)
            self.assertEqual(over["candidates_examined"], 1)
            self.assertTrue(over["truncated"])
            changed = list(view); changed[4], changed[3] = "-", "K"
            empty = index.query(database, "".join(changed), 0, top=1, budget=2)
            self.assertEqual(empty["matches"], [])
            self.assertEqual(empty["candidates_examined"], 0)
            self.assertFalse(empty["truncated"])

    def test_top_one_can_find_later_best_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, accepted = fixture(root, splits=("train",))
            index.build(manifest, accepted, root / "index")
            database = root / "index/actors.sqlite"
            views = actor()["observations"]
            with sqlite3.connect(database) as db:
                db.execute("UPDATE decisions SET observation=? WHERE ply=0", (index.pack_view(views[2]),))
                db.execute("UPDATE decisions SET observation=? WHERE ply=2", (index.pack_view(views[0]),))
            answer = index.query(database, views[0], 0, top=1, budget=2)
            self.assertEqual(answer["candidates_examined"], 2)
            self.assertEqual([(r["ply"], r["distance"]) for r in answer["matches"]], [(2, 0)])

    def test_equal_scores_keep_decision_id_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, accepted = fixture(root, splits=("train",))
            index.build(manifest, accepted, root / "index")
            database = root / "index/actors.sqlite"
            view = actor()["observations"][0]
            with sqlite3.connect(database) as db:
                db.execute("UPDATE decisions SET observation=?", (index.pack_view(view),))
            answer = index.query(database, view, 0, top=2, budget=2)
            self.assertEqual([r["decision_id"] for r in answer["matches"]], [1, 2])
            self.assertEqual([r["distance"] for r in answer["matches"]], [0, 0])


if __name__ == "__main__":
    unittest.main()
