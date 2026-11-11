"""Review the preserved deterministic read-back, without recompilation/policy."""
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-20261111"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    original = json.loads((OUT / "native-readback.json").read_text())
    assert sha(OUT / "prepare-first.py") == original["original_source_sha256"]
    assert sha(HERE / "build/probe.so") == original["probe_sha256"]
    prepare = load(HERE / "prepare.py", "safe_recapture_current_driver")
    oracle = load(ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py", "safe_recapture_existing_oracle")
    ref, chess = oracle.ref, oracle.ref.chess
    lib = prepare.library()
    fixtures = json.loads((OUT / "fixtures.json").read_text())["cases"]
    rows, recaptures = [], 0
    for item, record in zip(fixtures, original["rows"]):
        board = ref.FowBoard(None)
        board.turn = item["side"] == 0
        board.castling_rights = int(item["castle"], 16)
        board.ep_square = None if item["ep"] == -1 else item["ep"]
        board.halfmove_clock = item["halfmove"]
        for square, piece in enumerate(item["board"]):
            if piece != "-":
                board.set_piece_at(square, chess.Piece.from_symbol(piece))
        expected = oracle.reference(board, item["move"])
        assert expected == item["reference"]
        assert record["name"] == item["name"] and record["flags"] >= 0
        assert record["amended"] == bool(expected["risk"]) and not record["flags"] & 4
        post = board.copy(stack=False)
        post.push_uci(item["move"])
        for event in expected["captures"]:
            child = post.copy(stack=False)
            move = chess.Move.from_uci(event["reply"])
            child.push(move)
            flags = lib.astra_recapture_flags(oracle.board_string(child).encode(), 0 if child.turn else 1,
                int(child.clean_castling_rights()), child.ep_square if child.ep_square is not None else -1,
                child.halfmove_clock, move.to_square)
            assert flags in (0, 3)
            assert bool(flags & 1) == bool(event["legal_safe_recaptures"])
            recaptures += 1
        rows.append(record)
    assert len(fixtures) == len(rows) == 22
    assert not rows[0]["original"] and rows[0]["amended"]
    assert not rows[1]["original"] and not rows[1]["amended"]
    scope = json.loads((OUT / "patch-scope.json").read_text())
    source = prepare.NATIVE / "main.c"
    assert sha(source) == scope["original_main_sha256"]
    patch_bytes = gzip.decompress((HERE / "safe-recapture.patch.gz").read_bytes())
    with tempfile.TemporaryDirectory(dir=HERE / "build") as temp:
        folder = Path(temp)
        (folder / "src").mkdir()
        (folder / "src/main.c").write_bytes(source.read_bytes())
        (folder / "amend.patch").write_bytes(patch_bytes)
        result = subprocess.run(["patch", "--batch", "--forward", "-p1", "-i", str(folder / "amend.patch")],
                                cwd=folder, capture_output=True, text=True, check=True)
        assert sha(folder / "src/main.c") == scope["amended_main_sha256"]
        patched = (folder / "src/main.c").read_text()
        begin = patched.index("static void queen_risks(")
        end = patched.index("\n/* Diagnostics", begin)
        function = patched[begin:end].replace("static void queen_risks(", "static void astra_queen_risks(", 1)
        assert function in (HERE / "build/main_probe.c").read_text()
    mismatches = [row["name"] for row in rows if row["original"] != row["reference"]]
    report = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, cases=22,
        original_false_negatives=len(mismatches), amended_mismatches=0,
        optimized_exhaustive_course_recapture_checks=recaptures, changed_cases=mismatches,
        real_loss=dict(original=rows[0]["original"], amended=rows[0]["amended"]),
        sound_trade_control=dict(original=rows[1]["original"], amended=rows[1]["amended"]),
        patch_applies_to_exact_source=True, patched_function_matches_tested_copy=True,
        initial_run=dict(session=46625, observed_exit_code=1, failure="Reporter guessed10baseline mismatches; actual8. All22amended and recapture assertions were reached before that final count check. Raw per-case rows were not retained."),
        readback="Separate22-case deterministic helper invocation from unchanged compiled probe. No recompilation or policy replay. Raw results retained and reviewed here.",
        mismatch_reason="The unsafe-king-recapture fixtures also allow the bishop to capture the queen. The original best-capture helper already crosses its threshold through that second capture; cases retained unchanged.",
        source_pins={str(path): sha(path) for path in [Path(__file__), HERE / "prepare.py", OUT / "prepare-first.py",
            OUT / "native-readback.json", HERE / "safe_recapture.h", HERE / "bridge.c", HERE / "build/main_probe.c", HERE / "build/probe.so"]},
        limits=json.loads((OUT / "plan.json").read_text())["limits"])
    with (OUT / "component-result.json").open("x") as stream:
        json.dump(report, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ["passed", "cases", "original_false_negatives", "amended_mismatches", "optimized_exhaustive_course_recapture_checks"]}))


if __name__ == "__main__":
    main()
