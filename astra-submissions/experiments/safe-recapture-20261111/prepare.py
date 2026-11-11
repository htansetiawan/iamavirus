"""Isolated v38 helper conformance; never run a patched engine policy."""
from datetime import datetime, timezone
import ctypes as C
import difflib
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-20261111"
BUILD = HERE / "build"
NATIVE = ROOT / "astra-submissions/experiments/farsight-root-20261110/build/control/src"
ZIP = ROOT / "astra-submissions/iamavirus-v38-mist-c-allchildren.zip"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def library():
    lib = C.CDLL(str(BUILD / "probe.so"), mode=C.RTLD_LOCAL)
    lib.astra_initialize()
    lib.astra_flags.argtypes = [C.c_char_p, C.c_int, C.c_uint64, C.c_int, C.c_int, C.c_char_p, C.c_int]
    lib.astra_flags.restype = C.c_int
    lib.astra_recapture_flags.argtypes = [C.c_char_p, C.c_int, C.c_uint64, C.c_int, C.c_int, C.c_int]
    lib.astra_recapture_flags.restype = C.c_int
    return lib


def main():
    plan_path = OUT / "plan.json"
    plan = json.loads(plan_path.read_text())
    for path, expected in plan["source_pins"].items():
        assert sha(path) == expected, path
    BUILD.mkdir(exist_ok=False)
    with zipfile.ZipFile(ZIP) as archive:
        launchers = [name for name in archive.namelist() if name == "run.sh" or name.endswith("/run.sh")]
        assert len(launchers) == 1
        prefix = launchers[0][:-len("run.sh")]
        for path in NATIVE.iterdir():
            if path.is_file():
                assert archive.read(prefix + "src/" + path.name) == path.read_bytes(), path.name
    source = (NATIVE / "main.c").read_text()
    start = source.index("static void queen_risks(")
    end = source.index("\n/* Diagnostics", start)
    original = source[start:end]
    old_line = "if (is_attacked(&q, sq, us)) gain -= piece_pawns[p.piece[MOVE_FROM(l.moves[j])]];"
    new_line = "if (is_attacked(&q, sq, us) && astra_safe_recapture(&q, sq)) gain -= piece_pawns[p.piece[MOVE_FROM(l.moves[j])]];"
    assert original.count(old_line) == 1
    amended = original.replace("static void queen_risks(", "static void astra_queen_risks(", 1).replace(old_line, new_line)
    helpers = (HERE / "safe_recapture.h").read_text()
    insertion = source.index("/* Queen guard.")
    probe = source[:insertion] + helpers + "\n" + source[insertion:end] + "\n" + amended + source[end:]
    (BUILD / "main_probe.c").write_text(probe)
    production_helper = helpers.split("/* Independent native enumeration")[0].rstrip() + "\n"
    proposed = source[:insertion] + production_helper + "\n" + source[insertion:start] + original.replace(old_line, new_line) + source[end:]
    patch = "".join(difflib.unified_diff(source.splitlines(True), proposed.splitlines(True),
                                     fromfile="a/src/main.c", tofile="b/src/main.c"))
    with (HERE / "safe-recapture.patch.gz").open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            stream.write(patch.encode())
    save(OUT / "patch-scope.json", dict(original_main_sha256=sha(NATIVE / "main.c"),
        amended_main_sha256=hashlib.sha256(proposed.encode()).hexdigest(),
        patch_sha256=sha(HERE / "safe-recapture.patch.gz"),
        original_helper_unchanged_in_probe=True,
        difference="Add target-specific king-safe recapture helper; change one condition only in queen_risks. No material helper, terminal-capture or promotion change."))
    base = ["gcc", "-std=c11", "-O2", "-pthread", "-D_POSIX_C_SOURCE=199309L", "-shared", "-fPIC",
            "-I", str(BUILD), "-I", str(NATIVE), str(HERE / "bridge.c")]
    names = ["board", "belief", "movemodel", "cfr", "eval", "search", "gtcfr", "front", "sfeval"]
    command = base + [str(NATIVE / (name + ".c")) for name in names] + ["-lm", "-o", str(BUILD / "probe.so")]
    done = subprocess.run(command, text=True, capture_output=True, timeout=120)
    (OUT / "compile.stdout").write_text(done.stdout)
    (OUT / "compile.stderr").write_text(done.stderr)
    assert done.returncode == 0, done.stderr
    reference = load(ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py", "existing_course_ledger")
    ref, chess = reference.ref, reference.ref.chess
    fixtures = []

    def add(name, board, move):
        fixtures.append((name, board, move))

    replay_root = ROOT / "data/astra-spool/experience-catalogue-20261111/raw/games"
    actual = {}
    for name, game, ply in (("real-pinned-pawn", "ewav2dzr", 34), ("real-sound-trade", "do0s3j6i", 12)):
        replay = json.loads((replay_root / game / "replay.json").read_text())
        board = ref.FowBoard()
        for frame in replay["frames"][1:ply + 1]:
            board.push_uci(frame["move"])
        assert reference.board_string(board) == replay["frames"][ply]["board"]
        actual[name] = board
        add(name, board, replay["frames"][ply + 1]["move"])
    unpinned = actual["real-pinned-pawn"].copy(stack=False)
    unpinned.remove_piece_at(chess.E1)
    unpinned.set_piece_at(chess.G1, chess.Piece(chess.KING, chess.WHITE))
    unpinned.castling_rights = 0
    add("same-position-unpinned-control", unpinned, "d1d5")
    alternative = actual["real-pinned-pawn"].copy(stack=False)
    alternative.set_piece_at(chess.C4, chess.Piece(chess.BISHOP, chess.WHITE))
    add("second-safe-defender-control", alternative, "d1d5")
    no_recap = actual["real-pinned-pawn"].copy(stack=False)
    no_recap.remove_piece_at(chess.E4)
    no_recap.set_piece_at(chess.E2, chess.Piece(chess.KNIGHT, chess.WHITE))
    add("unguarded-queen-loss-control", no_recap, "d1d5")
    add("pinned-bishop", reference.position({"e1": "K", "e2": "B", "a3": "Q", "e8": "r", "d8": "q", "d3": "p", "h8": "k"}, True), "a3d3")
    add("pinned-knight", reference.position({"e1": "K", "e2": "N", "a3": "Q", "e8": "r", "c8": "q", "c3": "p", "h8": "k"}, True), "a3c3")
    king_case = {"g2": "K", "h4": "Q", "a8": "k", "h8": "r", "h3": "p"}
    add("unsafe-king-recapture", reference.position({**king_case, "f5": "b"}, True), "h4h3")
    add("safe-king-recapture-control", reference.position(king_case, True), "h4h3")
    add("safe-promotion-recapture", reference.position({"h1": "K", "h6": "Q", "g7": "P", "a8": "k", "d8": "q", "h8": "r"}, True), "h6h8")
    add("pinned-promotion-recapture", reference.position({"g1": "K", "h6": "Q", "g7": "P", "a8": "k", "h5": "q", "h8": "r", "g8": "r"}, True), "h6h8")
    originals = list(fixtures)
    for name, board, move in originals:
        m = chess.Move.from_uci(move)
        mirrored = chess.Move(chess.square_mirror(m.from_square), chess.square_mirror(m.to_square), promotion=m.promotion)
        add(name + "-mirror", board.mirror(), mirrored.uci())
    assert len(fixtures) == 22
    expected = [dict(name=name, board=reference.board_string(board), side=0 if board.turn else 1,
        castle=f"{int(board.clean_castling_rights()):016x}", ep=board.ep_square if board.ep_square is not None else -1,
        halfmove=board.halfmove_clock, move=move, reference=reference.reference(board, move))
        for name, board, move in fixtures]
    save(OUT / "fixtures.json", dict(cases=expected, threshold=4,
        scope="Frozen course-reference labels before invoking the native helper; constructed cases are not error-frequency estimates."))
    assert expected[0]["reference"]["risk"] == 1 and expected[1]["reference"]["risk"] == 0
    lib = library()
    results, recaptures = [], 0
    for item, (_, board, _) in zip(expected, fixtures):
        flags = lib.astra_flags(item["board"].encode(), item["side"], int(item["castle"], 16),
                               item["ep"], item["halfmove"], item["move"].encode(), 4)
        assert flags >= 0
        assert bool(flags & 2) == bool(item["reference"]["risk"]), (item, flags)
        assert not flags & 4
        post = board.copy(stack=False)
        post.push_uci(item["move"])
        for event in item["reference"]["captures"]:
            child = post.copy(stack=False)
            reply = chess.Move.from_uci(event["reply"])
            child.push(reply)
            result = lib.astra_recapture_flags(reference.board_string(child).encode(),
                0 if child.turn else 1, int(child.clean_castling_rights()),
                child.ep_square if child.ep_square is not None else -1, child.halfmove_clock, reply.to_square)
            assert result in (0, 3), (item["name"], result)
            assert bool(result & 1) == bool(event["legal_safe_recaptures"])
            recaptures += 1
        results.append(dict(name=item["name"], original_risk=bool(flags & 1),
                            amended_risk=bool(flags & 2), reference_risk=bool(item["reference"]["risk"])))
    save(OUT / "native-rows.json", results)
    mismatches = sum(r["original_risk"] != r["reference_risk"] for r in results)
    assert not results[0]["original_risk"] and results[0]["amended_risk"]
    assert not results[1]["original_risk"] and not results[1]["amended_risk"]
    save(OUT / "component-result.json", dict(passed=True, cases=22, original_false_negatives=mismatches,
        amended_mismatches=0, optimized_exhaustive_course_recapture_checks=recaptures,
        real_loss_original_risk=results[0]["original_risk"], real_loss_amended_risk=results[0]["amended_risk"],
        sound_trade_control=results[1], results=results,
        source_pins={str(path): sha(path) for path in [Path(__file__), HERE / "bridge.c", HERE / "safe_recapture.h",
            BUILD / "main_probe.c", BUILD / "probe.so", NATIVE / "main.c",
            ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py"]},
        compile_command=command, limits=plan["limits"]))
    print(json.dumps(dict(passed=True, cases=22, original_false_negatives=mismatches,
                         amended_mismatches=0, recapture_checks=recaptures)), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if not (OUT / "component-failure.json").exists():
            save(OUT / "component-failure.json", dict(at=datetime.now(timezone.utc).isoformat(), error=repr(error)))
        raise
