"""Prepare a current-source review patch; compile it but never play its policy."""
from datetime import datetime, timezone
import difflib
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-integration-20261111"
BUILD = HERE / "build"
ENGINE = ROOT.parent / "fowsearch-c"
COMMIT = "d2622531f5e704788b61da2b22cbbed23575f3e6"
NAMES = ["board", "belief", "movemodel", "cfr", "eval", "search", "gtcfr", "front", "sfeval", "main"]
FLAGS = ["-O2", "-pthread", "-D_POSIX_C_SOURCE=199309L"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open("x") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def load(path):
    spec = importlib.util.spec_from_file_location("existing_recapture_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert subprocess.check_output(["git", "-C", str(ENGINE), "rev-parse", "HEAD"], text=True).strip() == COMMIT
    assert not subprocess.check_output(["git", "-C", str(ENGINE), "diff", "HEAD", "--", "src"], text=True).strip()
    plan = json.loads((OUT / "plan.json").read_text())
    assert sha(Path(__file__).read_bytes()) == plan["runner_sha256"]
    for path, expected in plan["pins"].items():
        assert sha((ROOT / path).read_bytes()) == expected, path
    leases = json.loads((ROOT / "chatroom/cores.json").read_text())["allocation"]
    assert any(x.get("lease") == "422-recapture-integration" and x.get("cores") == [2, 3] for x in leases)
    assert not any(set(x.get("cores", [])) & {2, 3} for x in leases if x.get("lease") != "422-recapture-integration")
    os.sched_setaffinity(0, {2, 3})
    BUILD.mkdir(exist_ok=False)
    tree = BUILD / "tree"
    tree.mkdir()
    shutil.copytree(ENGINE / "src", tree / "src")
    shutil.copyfile(ENGINE / "arena/build.sh", tree / "build.sh")
    original = (tree / "src/main.c").read_text()
    helper = (ROOT / "astra-submissions/experiments/safe-recapture-20261111/safe_recapture.h").read_text().split("/* Independent native enumeration")[0].rstrip() + "\n"
    start = original.index("static void queen_risks(")
    end = original.index("\n/* Piece guard.", start)
    function = original[start:end]
    old = "if (is_attacked(&q, sq, us)) gain -= piece_pawns[p.piece[MOVE_FROM(l.moves[j])]];"
    new = "if (is_attacked(&q, sq, us) && astra_safe_recapture(&q, sq)) gain -= piece_pawns[p.piece[MOVE_FROM(l.moves[j])]];"
    assert function.count(old) == 1 and "double *ru" in function
    insertion = original.index("/* Queen guard.")
    amended = original[:insertion] + helper + "\n" + original[insertion:start] + function.replace(old, new) + original[end:]
    assert amended.replace(helper + "\n", "", 1).replace(new, old, 1) == original
    patch = "".join(difflib.unified_diff(original.splitlines(True), amended.splitlines(True), fromfile="a/src/main.c", tofile="b/src/main.c"))
    (HERE / "current-source.patch").write_text(patch)
    commands = []

    def command(label, argv, payload=None, required=True, timeout=15):
        before = time.monotonic()
        proc = subprocess.Popen(argv, cwd=tree, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
        expired = False
        try:
            stdout, stderr = proc.communicate(payload, timeout=timeout)
        except subprocess.TimeoutExpired:
            expired = True
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
        row = dict(label=label, argv=argv, exit_code=proc.returncode, seconds=time.monotonic() - before,
                   timed_out=expired, stdout=stdout, stderr=stderr)
        commands.append(row)
        with (OUT / "commands.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        assert not expired and (not required or proc.returncode == 0), row
        return row

    old_patch = gzip.decompress((ROOT / "astra-submissions/experiments/safe-recapture-20261111/safe-recapture.patch.gz").read_bytes()).decode()
    old_dry_run = command("archived-patch-no-fuzz-dry-run", ["patch", "--dry-run", "--batch", "--fuzz=0", "-p1"], old_patch, False)
    command("current-patch-no-fuzz-dry-run", ["patch", "--dry-run", "--batch", "--fuzz=0", "-p1"], patch)
    command("current-patch-apply", ["patch", "--batch", "--fuzz=0", "-p1"], patch)
    assert (tree / "src/main.c").read_text() == amended
    changed = [p.name for p in (tree / "src").iterdir() if p.is_file() and p.read_bytes() != (ENGINE / "src" / p.name).read_bytes()]
    assert changed == ["main.c"]
    bridge = r'''
#define main astra_unused_protocol_main
#include "main.c"
#undef main
__ORIGINAL__
int main(void) {
    fow_init(); zobrist_init();
    int count, threshold, case_id=0; size_t cap; double temp; char text[8];
    while (scanf("%d %zu %lf %d %7s", &count, &cap, &temp, &threshold, text)==5) {
        if (count<1 || count>4 || cap<1 || temp<=0) return 2;
        Position positions[4]; float weights[4]; Move move=0;
        for(int i=0;i<count;++i) {
            char board[65]; int side, ep, half; unsigned long long castle; double weight;
            if(scanf("%64s %d %llx %d %d %lf",board,&side,&castle,&ep,&half,&weight)!=6) return 3;
            if(pos_from_board_string(&positions[i],board,side,(bb_t)castle,ep)<0) return 4;
            positions[i].halfmove=half; weights[i]=(float)weight;
            MoveList moves; generate_moves(&positions[i],&moves); int found=0;
            for(int j=0;j<moves.count;++j) {char u[6];move_to_uci(moves.moves[j],u);if(strcmp(u,text)==0){if(i && move!=moves.moves[j])return 5;move=moves.moves[j];found=1;break;}}
            if(!found)return 6;
        }
        Belief b={0};b.items=positions;b.logw=weights;b.count=(size_t)count;b.us=positions[0].side;
        double old[3], updated[3], null_fitted, null_sharp;
        astra_original_queen_risks(&b,move,cap,temp,threshold,&old[0],&old[1],&old[2]);
        queen_risks(&b,move,cap,temp,threshold,&updated[0],&updated[1],&updated[2]);
        queen_risks(&b,move,cap,temp,threshold,&null_fitted,&null_sharp,NULL);
        printf("{\"case\":%d,\"original\":[%.17g,%.17g,%.17g],\"amended\":[%.17g,%.17g,%.17g],\"null\":[%.17g,%.17g]}\n",case_id++,old[0],old[1],old[2],updated[0],updated[1],updated[2],null_fitted,null_sharp);
    }
    return 0;
}
'''.replace("__ORIGINAL__", function.replace("static void queen_risks(", "static void astra_original_queen_risks(", 1))
    (tree / "src/probe.c").write_text(bridge)
    reference = load(ROOT / "astra-submissions/experiments/promotion-ledger-20261110/check.py")
    ref, chess = reference.ref, reference.ref.chess
    fixtures = json.loads((ROOT / "astra-submissions/analysis/safe-recapture-20261111/fixtures.json").read_text())["cases"]
    cases = [dict(name=f["name"], worlds=[f], logw=[0.0], move=f["move"], cap=1) for f in fixtures]
    original_board = ref.FowBoard(None)
    f = fixtures[0]
    original_board.turn = f["side"] == 0
    original_board.castling_rights = int(f["castle"], 16)
    original_board.ep_square = None if f["ep"] < 0 else f["ep"]
    original_board.halfmove_clock = f["halfmove"]
    for square, piece in enumerate(f["board"]):
        if piece != "-": original_board.set_piece_at(square, chess.Piece.from_symbol(piece))
    control = original_board.copy(stack=False); control.remove_piece_at(chess.E8)
    assert ref.observation(control, control.turn) == ref.observation(original_board, original_board.turn)
    other = dict(f, name="constructed-rook-removed", board=reference.board_string(control))
    other["reference"] = reference.reference(control, f["move"])
    assert other["reference"]["risk"] == 0
    for reverse in (False, True):
        for cap in (1, 2):
            worlds = [f, other][:: -1 if reverse else 1]
            cases.append(dict(name=f"weighted-reverse{int(reverse)}-cap{cap}", worlds=worlds, logw=[-5.0, -0.2], move=f["move"], cap=cap))
    lines = []
    for case in cases:
        lines.append(f"{len(case['worlds'])} {case['cap']} 2 4 {case['move']}")
        for item, weight in zip(case["worlds"], case["logw"]):
            lines.append(f"{item['board']} {item['side']} {item['castle']} {item['ep']} {item['halfmove']} {weight}")
    payload = "\n".join(lines) + "\n"
    (OUT / "component-input.txt").write_text(payload)
    save(OUT / "cases.json", cases)
    production = ["src/" + name + ".c" for name in NAMES]
    probe = ["src/" + name + ".c" for name in NAMES if name != "main"] + ["src/probe.c"]
    command("arena-build-script-gcc", ["bash", "build.sh"])
    shutil.copyfile(tree / "mist", tree / "mist-gcc")
    command("component-gcc-build", ["gcc", "-std=c11", *FLAGS, *probe, "-lm", "-o", "probe-gcc"])
    objects = tree / "objects"; objects.mkdir()
    for name in NAMES + ["probe"]:
        command("g++-c-object-" + name, ["g++", "-x", "c", "-std=c11", *FLAGS, "-c", "src/" + name + ".c", "-o", str(objects / (name + ".o"))])
    for label, names in (("mist-xc", NAMES), ("probe-xc", [n for n in NAMES if n != "main"] + ["probe"])):
        command(label + "-link", ["g++", "-pthread", *[str(objects / (n + ".o")) for n in names], "-lm", "-o", label])
    for label, names in (("mist-cpp", production), ("probe-cpp", probe)):
        command(label + "-build", ["g++", "-x", "c++", "-std=c++20", "-fpermissive", "-w", *FLAGS, *names, "-lm", "-o", label])
    runs = []
    for binary in ("probe-gcc", "probe-xc", "probe-cpp"):
        row = command(binary + "-component", [str(tree / binary)], payload)
        rows = [json.loads(line) for line in row["stdout"].splitlines()]
        assert len(rows) == len(cases)
        for i, (case, values) in enumerate(zip(cases, rows)):
            assert values["case"] == i and values["null"] == values["amended"][:2]
            stride = max(1, math.ceil(len(case["worlds"]) / case["cap"]))
            indices = range(0, len(case["worlds"]), stride)
            labels = [case["worlds"][j]["reference"]["risk"] for j in indices]
            weights = [struct.unpack("f", struct.pack("f", case["logw"][j]))[0] for j in indices]
            expected = [sum(y * math.exp(w / t) for y, w in zip(labels, weights)) / sum(math.exp(w / t) for w in weights) for t in (2.0, 1.0)]
            expected.append(sum(labels) / len(labels))
            assert all(abs(a - b) < 1e-12 for a, b in zip(values["amended"], expected)), (case["name"], values, expected)
        runs.append(dict(binary=binary, sha256=sha((tree / binary).read_bytes()), rows=rows))
    assert all(r["rows"] == runs[0]["rows"] for r in runs)
    # The probe is test-only. Recheck that the production snapshot has one changed source.
    for path, expected in plan["engine_sources"].items():
        assert sha((ENGINE / path).read_bytes()) == expected
    save(OUT / "result.json", dict(passed=True, at=datetime.now(timezone.utc).isoformat(), engine_commit=COMMIT,
        original_main_sha256=sha(original.encode()), amended_main_sha256=sha(amended.encode()),
        patch_sha256=sha(patch.encode()), original_patch_clean_application=old_dry_run["exit_code"] == 0,
        production_compiler_paths=3, component_cases=len(cases), original_fixtures=len(fixtures),
        weighted_cases=len(cases)-len(fixtures), compiler_component_outputs_identical=True,
        production_changed_sources=changed, runs=runs,
        scope="Current-source build and guard arithmetic only. No production binary was started, no backend or policy search, no strength result.",
        preserved="Existing terminal-aware enemy-capture clause, uniform output, other helpers, all prior failed playing gates."))
    print(json.dumps({"passed": True, "compiler_paths": 3, "component_cases": len(cases), "policy_runs": 0}))


if __name__ == "__main__":
    main()
