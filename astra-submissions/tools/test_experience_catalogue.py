"""Source binding and no-label-feedback contracts for the analyst catalogue."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalogue = load("catalogue_test_subject", "experience_catalogue.py")
old = load("existing_actor_fixtures", "test_experience_index.py")


def logical(answer):
    return {key: value for key, value in answer.items() if key != "elapsed_ms"}


def setup(root):
    manifest, accepted = old.fixture(root)
    old.index.build(manifest, accepted, root / "actors")
    actor_db = root / "actors/actors.sqlite"
    rows = []
    for number in range(2):
        game = f"game{number:04d}"
        # A source-binding fixture, not a rule-conformance chess replay.
        replay = dict(id=game, reason="King capturable", frames=[
            dict(ply=0, move=None), dict(ply=1, move="h2h3"),
            dict(ply=2, move="g8f6"), dict(ply=3, move="h3h4")])
        path = root / "raw" / game / "replay.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(replay))
        source = hashlib.sha256(path.read_bytes()).hexdigest()
        label = dict(kind="king_walk" if number == 0 else "king_bait", move="h3h4",
                     safe_moves=["e1d1"], forced_one_ply_loss=False,
                     all_killers_hidden=number == 0, material_before=-5,
                     killers=[dict(piece="R" if number == 0 else "N", square="h8",
                                   hidden_before=number == 0, own_screen_released=False)])
        for side in ("white", "black"):
            rows.append(dict(id=game, side=side, source_sha256=source, plies=3,
                             terminal_motif=label if side == "white" else None))
        with sqlite3.connect(actor_db) as db:
            db.execute("UPDATE episodes SET source_sha256=? WHERE game=?", (source, game))
    rows_path = root / "rows.json"
    rows_path.write_text(json.dumps(rows))
    cat_db = root / "catalogue.sqlite"
    return actor_db, rows, rows_path, cat_db


class CatalogueTests(unittest.TestCase):
    def test_role_facets_and_all_seat_sources_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, rows_path, db = setup(root)
            result = catalogue.build(rows_path, root / "raw", db)
            self.assertEqual((result["games"], result["seats"], result["terminal_examples"]), (2, 4, 2))
            answer = catalogue.browse(db, kind="king_walk", attacker="R", all_hidden=True, forced=False)
            self.assertEqual([r["game"] for r in answer["matches"]], ["game0000"])
            self.assertTrue(answer["analyst_only"])
            self.assertEqual(catalogue.browse(db, kind="king_walk", attacker="N")["matches"], [])
            self.assertEqual(catalogue.browse(db, forced=True)["matches"], [])
            with self.assertRaises(ValueError):
                catalogue.browse(db, attacker="duck")

    def test_labels_attach_only_to_exact_predecision_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actors, _, rows, db = setup(root)
            catalogue.build(rows, root / "raw", db)
            view = old.actor()["observations"][0]
            before = catalogue.actors.query(actors, view, 0)
            after = catalogue.query(actors, db, view, 0)
            self.assertEqual(logical(before), logical(after["actor_result"]))
            ids = {row["ply"]: str(row["decision_id"]) for row in before["matches"]}
            self.assertEqual(after["oracle_annotations"][ids[0]]["status"], "no_terminal_label_at_this_decision")
            self.assertEqual(after["oracle_annotations"][ids[2]]["status"], "labelled_terminal")
            self.assertEqual(after["oracle_annotations"][ids[2]]["oracle_label"]["kind"], "king_walk")
            with sqlite3.connect(actors) as conn:
                conn.execute("UPDATE episodes SET source_sha256=?", ("0" * 64,))
            stale = catalogue.query(actors, db, view, 0)
            self.assertEqual(logical(before), logical(stale["actor_result"]))
            self.assertTrue(all(v["status"] == "source_mismatch" and v["oracle_label"] is None
                                for v in stale["oracle_annotations"].values()))

    def test_label_mutation_cannot_change_actor_rank_or_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actors, _, rows, db = setup(root)
            catalogue.build(rows, root / "raw", db)
            actor_bytes = actors.read_bytes()
            view = old.actor()["observations"][0]
            before = catalogue.query(actors, db, view, 0)
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE motifs SET label_json=?", (json.dumps({"fake_oracle_value": 1e90}),))
            changed = catalogue.query(actors, db, view, 0)
            self.assertEqual(logical(before["actor_result"]), logical(changed["actor_result"]))
            self.assertNotEqual(before["oracle_annotations"], changed["oracle_annotations"])
            self.assertEqual(actors.read_bytes(), actor_bytes)

    def test_no_heldout_or_excluded_reference_can_be_resurrected_by_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actors, _, rows, db = setup(root)
            catalogue.build(rows, root / "raw", db)
            answer = catalogue.query(actors, db, old.actor()["observations"][0], 0,
                                     exclude_game="game0000")
            self.assertEqual(answer["actor_result"]["matches"], [])
            self.assertEqual(answer["oracle_annotations"], {})

    def test_source_or_row_validation_failure_leaves_no_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, rows, rows_path, db = setup(root)
            bad_source = copy.deepcopy(rows); bad_source[0]["source_sha256"] = "0" * 64
            wrong_seat = copy.deepcopy(rows); wrong_seat[0]["side"] = "black"
            bad_kind = copy.deepcopy(rows); bad_kind[0]["terminal_motif"]["kind"] = "player-specific-script"
            cases = (bad_source, wrong_seat, bad_kind, rows + [rows[0]])
            for sample in cases:
                with self.subTest(sample=cases.index(sample)):
                    rows_path.write_text(json.dumps(sample))
                    with self.assertRaises(ValueError):
                        catalogue.build(rows_path, root / "raw", db)
                    self.assertFalse(db.exists())

    def test_existing_database_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, rows, db = setup(root)
            catalogue.build(rows, root / "raw", db)
            original = db.read_bytes()
            with self.assertRaises(ValueError):
                catalogue.build(rows, root / "raw", db)
            self.assertEqual(db.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
