"""Review current-source integration artifacts; do not invoke any native binary."""
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-integration-20261111"
ENGINE = ROOT.parent / "fowsearch-c"


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    result = json.loads((OUT / "result.json").read_text())
    plan = json.loads((OUT / "plan-corrected.json").read_text())
    assert result["passed"] and result["engine_commit"] == plan["engine_commit"]
    assert sha((HERE / "check.py").read_bytes()) == plan["runner_sha256"]
    for path, expected in plan["pins"].items():
        assert sha((ROOT / path).read_bytes()) == expected, path
    patch = (HERE / "current-source.patch").read_bytes()
    assert sha(patch) == result["patch_sha256"]
    with tempfile.TemporaryDirectory(dir=HERE / "build") as d:
        p = Path(d); (p / "src").mkdir()
        source = (ENGINE / "src/main.c").read_bytes()
        assert sha(source) == result["original_main_sha256"]
        (p / "src/main.c").write_bytes(source)
        applied = subprocess.run(["patch", "--batch", "--fuzz=0", "-p1"], input=patch, cwd=p, capture_output=True, timeout=10)
        assert applied.returncode == 0 and b"fuzz" not in applied.stdout
        amended = (p / "src/main.c").read_bytes()
        assert sha(amended) == result["amended_main_sha256"]
        helper = (ROOT / "astra-submissions/experiments/safe-recapture-20261111/safe_recapture.h").read_bytes().split(b"/* Independent native enumeration")[0].rstrip() + b"\n"
        assert amended.count(helper + b"\n") == 1
        stripped = amended.replace(helper + b"\n", b"", 1)
        new = b"if (is_attacked(&q, sq, us) && astra_safe_recapture(&q, sq)) gain -="
        old = b"if (is_attacked(&q, sq, us)) gain -="
        assert stripped.count(new) == 1 and stripped.replace(new, old, 1) == source
        assert b"double *rt, double *ru)" in stripped
    # Native source snapshot files other than the intended main.c remain exact.
    for path, expected in plan["engine_sources"].items():
        data = (HERE / "build/corrected/tree" / path).read_bytes()
        assert sha(data) == (result["amended_main_sha256"] if path == "src/main.c" else expected)
        assert sha((ENGINE / path).read_bytes()) == expected
    commands = [json.loads(line) for line in (OUT / "commands.jsonl").read_text().splitlines()]
    assert len(commands) == 23 and len({c["label"] for c in commands}) == 23
    assert all(not c["timed_out"] for c in commands)
    assert commands[0]["label"] == "archived-patch-no-fuzz-dry-run" and commands[0]["exit_code"] == 1
    assert all(c["exit_code"] == 0 for c in commands[1:])
    assert [c["label"] for c in commands if c["label"].endswith("-component")] == ["probe-gcc-component", "probe-xc-component", "probe-cpp-component"]
    assert not any(Path(c["argv"][0]).name.startswith(("mist", "stockfish")) for c in commands)
    path = ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py"
    spec = importlib.util.spec_from_file_location("existing_course_reference", path)
    oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
    ref, chess = oracle.ref, oracle.ref.chess
    cases = json.loads((OUT / "cases.json").read_text())
    originals = json.loads((ROOT / "astra-submissions/analysis/safe-recapture-20261111/fixtures.json").read_text())["cases"]
    assert len(cases) == 26 and [c["worlds"][0] for c in cases[:22]] == originals
    expected = []; worlds_checked = 0
    for case in cases:
        labels = []
        for item in case["worlds"]:
            b = ref.FowBoard(None); b.turn = item["side"] == 0
            b.castling_rights = int(item["castle"], 16)
            b.ep_square = None if item["ep"] < 0 else item["ep"]
            b.halfmove_clock = item["halfmove"]
            for square, piece in enumerate(item["board"]):
                if piece != "-": b.set_piece_at(square, chess.Piece.from_symbol(piece))
            assert oracle.reference(b, case["move"]) == item["reference"]
            labels.append(item["reference"]["risk"]); worlds_checked += 1
        stride = (len(labels) + case["cap"] - 1) // case["cap"]
        selected = list(range(0, len(labels), stride))
        weights = [Decimal.from_float(struct.unpack("f", struct.pack("f", case["logw"][i]))[0]) for i in selected]
        with localcontext() as context:
            context.prec = 50
            row = []
            for divisor in (Decimal(2), Decimal(1)):
                masses = [(w / divisor).exp() for w in weights]
                row.append(float(sum(Decimal(labels[i]) * m for i, m in zip(selected, masses)) / sum(masses)))
            row.append(float(sum(Decimal(labels[i]) for i in selected) / len(selected)))
        expected.append(row)
    for run in result["runs"]:
        command = next(c for c in commands if c["label"] == run["binary"] + "-component")
        assert [json.loads(line) for line in command["stdout"].splitlines()] == run["rows"]
        assert sha((HERE / "build/corrected/tree" / run["binary"]).read_bytes()) == run["sha256"]
        for i, row in enumerate(run["rows"]):
            assert row["case"] == i and row["null"] == row["amended"][:2]
            assert all(abs(a - b) < 1e-12 for a, b in zip(row["amended"], expected[i]))
    checked = dict(passed=True, source_pins=len(plan["pins"]), native_sources_unchanged=len(plan["engine_sources"]),
                   course_world_checks=worlds_checked, compiler_cases=3 * len(cases), preserved_uniform_interface=True,
                   patch_exactly_one_condition_plus_unchanged_helper=True, required_commands_passed=len(commands)-1,
                   policy_or_backend_invocations=0, source_sha256=sha(Path(__file__).read_bytes()),
                   result_sha256=sha((OUT / "result.json").read_bytes()),
                   limits="Reused fixtures and constructed arithmetic; no performance or strength evidence. Original preparations and prior failed playing gates remain unchanged.")
    with (OUT / "review.json").open("x") as f:
        json.dump(checked, f, indent=2); f.write("\n")
    print(json.dumps(checked))


if __name__ == "__main__": main()
