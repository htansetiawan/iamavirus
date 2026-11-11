"""Post-hoc descriptive checking-victim contexts; no causal/promotion test."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "astra-submissions/analysis/king-capture-curriculum-20261111"


def victim_checks(inputs):
    move, victim = inputs["candidate"], inputs["victim"]
    df = ord(move[0]) - ord(move[2])
    dr = int(move[1]) - int(move[3])
    assert max(abs(df), abs(dr)) == 1
    return (victim == "Q" or victim == "R" and (df == 0 or dr == 0)
            or victim == "B" and abs(df) == abs(dr)
            or victim == "P" and abs(df) == 1 and dr == (1 if inputs["side"] == 1 else -1))


def main():
    result = json.loads((OUT / "result.json").read_text())
    path = Path(result["output"])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == result["output_sha256"]
    groups = defaultdict(lambda: dict(offers=0, taken=0, games=set(), decisions=set()))
    with gzip.open(path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            inputs, target, meta = row["inputs"], row["targets"], row["metadata"]
            if not target["all_cover_hidden"] or not target["avoidable"]:
                continue
            checking = victim_checks(inputs)
            for key in ((checking, "all"), (checking, inputs["victim"])):
                group = groups[key]
                group["offers"] += 1
                group["taken"] += int(target["played"])
                group["games"].add(meta["game"])
                group["decisions"].add((meta["game"], meta["side"], meta["ply"]))
    panels = [dict(victim_checks=check, victim=piece, offers=g["offers"], taken=g["taken"],
                   games=len(g["games"]), decisions=len(g["decisions"]))
              for (check, piece), g in sorted(groups.items())]
    output = dict(status="post-hoc descriptive analysis; no causal or promotion gate",
        source_sha256=result["output_sha256"], script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        panels=panels, limits=["Offers are candidate actions, and can repeat within the same game/decision.",
            "Checking/quiet offers arise in different positions and opponent mixes; no randomized causal comparison.",
            "Victim attack geometry uses its observed role and adjacent-square relation only.",
            "All records were inspected; no fit, untouched holdout, new strategy or strength estimate."])
    with (OUT / "offer-contexts.json").open("x") as stream:
        json.dump(output, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps(output, indent=1))


if __name__ == "__main__":
    main()
