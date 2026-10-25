import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_context_backoff as backoff


class ContextBackoffTests(unittest.TestCase):
    def test_black_view_is_rank_reflected_and_color_canonical(self):
        white = "RNBQKBNRPPPPPPPP----------------????????????????????????????????"
        black = "????????????????????????????????----------------pppppppprnbqkbnr"
        self.assertEqual(backoff.canonical_view(white, 0), backoff.canonical_view(black, 1))

    def test_black_actions_rank_flip_to_white_relative_coordinates(self):
        self.assertEqual(backoff.canonical_move("e7e5", 1), "e2e4")
        self.assertEqual(backoff.canonical_move("g8f6", 1), "g1f3")
        self.assertEqual(backoff.canonical_move("e2e4", 0), "e2e4")


if __name__ == "__main__":
    unittest.main()
