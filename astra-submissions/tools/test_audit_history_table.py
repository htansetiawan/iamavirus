import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_history_table as audit


class HistoryTableAuditTests(unittest.TestCase):
    def test_hashes_match_v35_c_reference_vector(self):
        view = "RNBQKBNRPPPPPPPP----------------????????????????????????????????"
        self.assertEqual(audit.view_hash(view), 0x55B81F2A819509DF)
        h = audit.history_mix(0, audit.view_hash(view))
        self.assertEqual(h, 0x55088648E89D2B58)
        move = audit.move_code("a2a4")
        self.assertEqual(move, 26120)
        self.assertEqual(audit.history_mix(h, move), 0x6D1DF7F231FAB26D)

    def test_reads_and_merges_sorted_table_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "table.bin"
            rows = [(11, 20, 2), (11, 20, 3), (11, 21, 4), (12, 22, 1)]
            path.write_bytes(audit.HEADER.pack(b"MISTHIST", 1, len(rows)) +
                             b"".join(audit.RECORD.pack(*row) for row in rows))
            table = audit.read_table(path)
        self.assertEqual(table[11], (9, {20: 5, 21: 4}))
        self.assertEqual(table[12], (1, {22: 1}))

    def test_replay_updates_each_players_information_history(self):
        white0 = "RNBQKBNRPPPPPPPP----------------????????????????????????????????"
        black0 = "????????????????????????????????----------------pppppppprnbqkbnr"
        white1 = white0
        black1 = black0
        white2 = white1
        black2 = black1
        frames = [
            {"white": white0, "black": black0, "move": None},
            {"white": white1, "black": black1, "move": "a2a4"},
            {"white": white2, "black": black2, "move": "a7a5"},
        ]
        wh = audit.history_mix(0, audit.view_hash(white0))
        table = {wh: (3, {audit.move_code("a2a4"): 3})}
        stats = {"white": audit.empty_stats(), "black": audit.empty_stats()}
        replay = {"white": "white", "black": "black", "frames": frames}
        self.assertEqual(audit.analyze_game(replay, table, stats, 3), 2)
        self.assertEqual(stats["white"]["lookup_eligible_n_ge_3"], 1)
        self.assertEqual(stats["white"]["actual_action_in_table"], 1)
        self.assertEqual(stats["black"]["decisions"], 1)


if __name__ == "__main__":
    unittest.main()
