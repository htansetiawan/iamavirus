"""Two frozen, unchanged-v38 replays; amended helper used only after selection."""
import argparse
import ctypes as C
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "astra-submissions/analysis/safe-recapture-20261111"
SPOOL = ROOT / "data/astra-spool/safe-recapture-20261111"
LEASE = "417-safe-recapture"


def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependencies():
    plan = read(OUT / "plan.json")
    for path, expected in plan["source_pins"].items():
        assert sha(path) == expected, path
    for path, expected in read(OUT / "replay-preflight.json")["source_pins"].items():
        assert sha(path) == expected, path
    assert read(OUT / "component-result.json")["passed"]
    return plan


def run():
    plan = dependencies()
    config = plan["fixed_replay"]
    leases = read(ROOT / "chatroom/cores.json")["allocation"]
    assert any(x.get("lease") == LEASE and x["cores"] == config["cores"] for x in leases)
    assert not any(set(x.get("cores", [])) & set(config["cores"]) for x in leases if x.get("lease") != LEASE)
    assert not SPOOL.exists()
    SPOOL.mkdir()
    os.sched_setaffinity(0, set(config["cores"]))
    driver = load(ROOT / "astra-submissions/experiments/farsight-root-20261110/study.py", "existing_v38_replay_driver")
    save(OUT / "replay-started.json", dict(at=now(), pid=os.getpid(), plan_sha256=sha(OUT / "plan.json")))
    start = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("600-second batch cap")))
    signal.alarm(config["batch_seconds"])
    receipts = []
    try:
        for role in ("loss", "control"):
            case = plan["selected_pair"][role]
            replay = read(ROOT / f"data/astra-spool/experience-catalogue-20261111/raw/games/{case['game']}/replay.json")
            # This projection is the sole actor input. Future/true boards and
            # opponent actions are never added to its input or environment.
            feed, forced, clocks = driver.projection(replay, case["root_ply"], 0)
            folder = SPOOL / role
            env = driver.environment(folder, forced, clocks)
            env["FOW_SEED"] = str(config["seed"])
            stdout, stderr = driver.run_native(Path(config["existing_observer_binary"]), folder, feed, env,
                                               config["process_seconds"])
            moves = [line[5:] for line in stdout.splitlines() if line.startswith("move ")]
            assert len(moves) == len(forced) + 1 and moves[:-1] == forced
            assert [float(v) for v in re.findall(r"astra-prefix: clock=([\d.]+)", stderr)] == clocks
            assert (folder / "population.json").is_file() and (folder / "targets.jsonl").is_file()
            assert sum(p.stat().st_size for p in SPOOL.rglob("*") if p.is_file()) <= config["maximum_private_bytes"]
            receipt = dict(role=role, game=case["game"], root_ply=case["root_ply"], chosen=moves[-1],
                terminal=read(folder / "terminal.json"),
                files={str(p.relative_to(SPOOL)): sha(p) for p in folder.iterdir() if p.is_file()})
            receipts.append(receipt)
            save(OUT / f"{role}-replay.json", receipt)
            print(json.dumps(dict(role=role, chosen=moves[-1], status="complete")), flush=True)
        save(OUT / "replay-completion.json", dict(at=now(), seconds=time.monotonic()-start, cases=receipts))
    except BaseException as error:
        save(OUT / "replay-failure.json", dict(at=now(), error=repr(error), seconds=time.monotonic()-start))
        raise
    finally:
        signal.alarm(0)


class Moves(C.Structure):
    _fields_ = [("moves", C.c_uint16 * 256), ("count", C.c_int)]


class Front(C.Structure):
    _fields_ = [("us", C.c_int), ("their", C.c_int * 6), ("castle", C.c_uint64),
                ("config", C.c_uint64 * 1024), ("seen", C.c_int * 1024), ("configs", C.c_int)]


def encoded(text):
    source = ord(text[0])-97 + 8*(int(text[1])-1)
    target = ord(text[2])-97 + 8*(int(text[3])-1)
    promotion = "pnbrqk".index(text[4]) if len(text) == 5 else 6
    return source | target << 6 | promotion << 12


def decoded(move):
    source, target, promotion = move & 63, (move >> 6) & 63, (move >> 12) & 7
    text = chr(97+source%8)+str(source//8+1)+chr(97+target%8)+str(target//8+1)
    return text + ("pnbrqk"[promotion] if promotion != 6 else "")


def mask(rows, amended=False):
    key = "amended_queen" if amended else "original_queen"
    fitted = [r["king"][0] + .9*r[key][0] for r in rows]
    sharp = [r["king"][1] + .9*r[key][1] for r in rows]
    excluded = [s > min(sharp)+.02 or f > min(fitted)+.02 for f,s in zip(fitted,sharp)]
    fallback = all(excluded)
    if fallback: excluded = [s > min(sharp)+.02 for s in sharp]
    return dict(excluded=[r["move"] for r, flag in zip(rows, excluded) if flag],
                sharp_only_fallback=fallback, least_fitted=min(fitted), least_sharp=min(sharp))


def analyze():
    plan = dependencies()
    assert read(OUT / "replay-completion.json")
    prepare = load(HERE / "prepare.py", "safe_recapture_fixed_probe")
    lib = prepare.library()
    for name, args, result in [
        ("front_init", [C.POINTER(Front), C.c_int], None),
        ("front_see", [C.POINTER(Front), C.c_char_p], None),
        ("front_play", [C.POINTER(Front), C.c_char_p, C.c_uint16], None),
        ("front_lead", [C.POINTER(Front), C.c_char_p], C.c_int),
        ("front_repeats", [C.POINTER(Front), C.c_char_p, C.POINTER(Moves), C.POINTER(C.c_uint16)], C.c_int),
        ("view_moves", [C.c_char_p, C.c_int, C.c_uint64, C.POINTER(Moves)], C.c_int),
        ("pos_from_board_string", [C.c_void_p,C.c_char_p,C.c_int,C.c_uint64,C.c_int],C.c_int),
        ("generate_moves", [C.c_void_p,C.POINTER(Moves)],None),
        ("make_move", [C.c_void_p,C.c_uint16,C.c_void_p],None),
        ("mover_left_king_capturable", [C.c_void_p],C.c_int)]:
        fn = getattr(lib, name); fn.argtypes = args; fn.restype = result
    results = []
    for role in ("loss", "control"):
        case = plan["selected_pair"][role]
        replay = read(ROOT / f"data/astra-spool/experience-catalogue-20261111/raw/games/{case['game']}/replay.json")
        population = read(SPOOL / role / "population.json")
        worlds = population["worlds"]
        assert population["count"] == len(worlds) and population["us"] == 0 and worlds
        front = Front(); lib.front_init(C.byref(front), 0)
        for ply in range(case["root_ply"]+1):
            view = replay["frames"][ply]["white"].encode()
            lib.front_see(C.byref(front), view)
            if ply % 2 == 0 and ply < case["root_ply"]:
                lib.front_play(C.byref(front), view, encoded(replay["frames"][ply+1]["move"]))
        allowed = Moves(); assert lib.view_moves(view, 0, front.castle, C.byref(allowed)) > 0
        actions = [decoded(allowed.moves[i]) for i in range(allowed.count)]
        repeats = (C.c_uint16*256)()
        lead = lib.front_lead(C.byref(front), view)
        repeated = [decoded(repeats[i]) for i in range(lib.front_repeats(C.byref(front), view, C.byref(allowed), repeats))] if lead >= 2 else []
        stride = max(1, (len(worlds)+19999)//20000)
        sums = [[0.,0.] for _ in range(3*len(actions))]
        totals = [0.,0.]
        flags_path = SPOOL / role / "strided-flags.jsonl.gz"
        with flags_path.open("xb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as packed:
            for i in range(0,len(worlds),stride):
                world = worlds[i]
                weights = (math.exp(world["logw"]/population["temperature"]), math.exp(world["logw"]))
                flags = []
                for a, action in enumerate(actions):
                    flag = lib.astra_flags(world["board"].encode(), world["side"], int(world["castle"],16),
                        world["ep"], world["halfmove"], action.encode(), 4)
                    assert flag >= 0, (role,i,action,flag)
                    flags.append(flag)
                    for bit in range(3):
                        if flag & (1 << bit):
                            for w in range(2): sums[3*a+bit][w] += weights[w]
                for w in range(2): totals[w] += weights[w]
                packed.write((json.dumps(dict(index=i, flags=flags),separators=(",",":"))+"\n").encode())
        rows = [dict(move=action, original_queen=[v/t for v,t in zip(sums[3*a],totals)],
                     amended_queen=[v/t for v,t in zip(sums[3*a+1],totals)],
                     king=[v/t for v,t in zip(sums[3*a+2],totals)]) for a,action in enumerate(actions)]
        old, amended = mask(rows), mask(rows,True)
        searched = {a["move"] for sample in population["samples"] for a in sample["actions"]}
        expected = set(actions)-set(old["excluded"])-set(repeated)
        assert searched == expected, (role, sorted(searched ^ expected))
        raw_weights = [[math.exp(w["logw"]/population["temperature"]),math.exp(w["logw"])] for w in worlds]
        denom = [sum(w[k] for w in raw_weights) for k in range(2)]
        true = replay["frames"][case["root_ply"]]["board"]
        matching = [i for i,w in enumerate(worlds) if w["board"] == true]
        board_mass = [sum(raw_weights[i][k] for i in matching)/denom[k] for k in range(2)]
        reply = replay["frames"][case["root_ply"]+2]["move"]
        root_move, reply_move = encoded(case["recorded_move"]), encoded(reply)
        support = []
        reply_source = reply_move & 63
        # Oversized opaque buffers hold the exact archive's Position (216 B)
        # and Undo (40 B); only original native routines interpret them.
        for i,world in enumerate(worlds):
            if world["board"][reply_source] != true[reply_source]: continue
            position = C.create_string_buffer(512); undo = C.create_string_buffer(128)
            assert lib.pos_from_board_string(position,world["board"].encode(),world["side"],
                int(world["castle"],16),world["ep"]) == 0
            lib.make_move(position,root_move,undo)
            if lib.mover_left_king_capturable(position): continue
            replies = Moves(); lib.generate_moves(position,C.byref(replies))
            if reply_move not in replies.moves[:replies.count]: continue
            lib.make_move(position,reply_move,undo)
            if not lib.mover_left_king_capturable(position): support.append(i)
        support_set = set(support)
        support_path = SPOOL / role / "recorded-capture-support.json.gz"
        with support_path.open("xb") as raw, gzip.GzipFile(filename="",fileobj=raw,mode="wb",mtime=0) as packed:
            packed.write(json.dumps(dict(reply=reply,indices=support),separators=(",",":")).encode())
        capture_mass = [sum(raw_weights[i][k] for i in support)/denom[k] for k in range(2)]
        changed = [r for r in rows if r["original_queen"] != r["amended_queen"]]
        receipt = read(OUT / f"{role}-replay.json")
        result = dict(role=role,game=case["game"],root_ply=case["root_ply"],chosen=receipt["chosen"],
            recorded=case["recorded_move"],population=len(worlds),stride=stride,
            measured_worlds=len(range(0,len(worlds),stride)),unique_sampled_worlds=len(population["samples"]),
            true_placement_count=len(matching),true_placement_mass_fitted_sharp=board_mass,
            true_placement_sample_indices=[s["index"] for s in population["samples"] if s["index"] in set(matching)],
            recorded_reply=reply,recorded_capture_support=len(support),
            recorded_capture_mass_fitted_sharp=capture_mass,
            recorded_capture_sample_indices=[s["index"] for s in population["samples"] if s["index"] in support_set],
            recorded_capture_sample_weight=sum(s["weight"] for s in population["samples"] if s["index"] in support_set),
            private_capture_support_sha256=sha(support_path),
            front_lead=lead,repeat_excluded=repeated,rows=rows,original_mask=old,amended_mask=amended,
            baseline_mask_reproduces_searched_actions=True,changed_queen_rows=changed,
            recorded_row=next(r for r in rows if r["move"] == case["recorded_move"]),
            private_flags_sha256=sha(flags_path),private_population_sha256=sha(SPOOL / role / "population.json"))
        save(OUT / f"{role}-fixed-population.json",result)
        results.append(result)
        print(json.dumps(dict(role=role,population=len(worlds),changed_rows=len(changed),
            recorded_old=result["recorded_row"]["original_queen"],recorded_amended=result["recorded_row"]["amended_queen"])),flush=True)
    save(OUT / "fixed-population-result.json", dict(at=now(),cases=results,limits=plan["limits"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("action",choices=("run","analyze"))
    action = parser.parse_args().action
    try: globals()[action]()
    except BaseException as error:
        path = OUT / f"{action}-failure.json"
        if not path.exists(): save(path,dict(at=now(),error=repr(error)))
        raise
