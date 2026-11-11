"""Check the selected move's threat geometry in the already saved worlds."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"astra-submissions/analysis/decision-tradeoff-20261111"


def main():
    path=ROOT/"astra-submissions/experiments/farsight-root-20261110/audit.py"
    spec=importlib.util.spec_from_file_location("existing_world_decoder",path)
    decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    result=json.loads((OUT/"result.json").read_text());case=next(c for c in result["cases"] if c["role"]=="loss")
    source=Path(next(p for p in case["source_hashes"] if p.endswith("population.json")))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==case["source_hashes"][str(source)]
    population=json.loads(source.read_text());rows=[]
    for sample in population["samples"]:
        board=decoder.world_board(population["worlds"][sample["index"]])
        move=decoder.ref.chess.Move.from_uci(case["chosen"]);assert move in decoder.ref.fow_moves(board)
        us=board.turn;board.push(move);king=board.king(not us);assert king is not None
        attacks_king=king in board.attacks(move.to_square)
        view=decoder.ref.observation(board,not us)
        rows.append(dict(index=sample["index"],weight=sample["weight"]/(case["raw_chance_mass"]),
            queen_attacks_king=attacks_king,queen_hidden_in_opponent_current_view=view[move.to_square]=="?"))
    receipt=dict(rows=rows,queen_attack_worlds=sum(r["queen_attacks_king"] for r in rows),
        queen_attack_weight=math.fsum(r["weight"] for r in rows if r["queen_attacks_king"]),
        hidden_queen_attack_worlds=sum(r["queen_attacks_king"] and r["queen_hidden_in_opponent_current_view"] for r in rows),
        hidden_queen_attack_weight=math.fsum(r["weight"] for r in rows if r["queen_attacks_king"] and r["queen_hidden_in_opponent_current_view"]),
        actual_world=next(r for r in rows if r["index"]==case["actual_world"]["index"]),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitation="Current visibility is not the opponent's full knowledge. History can reveal or imply a hidden attack. No threat-awareness, acceptance, causal benefit or strength claim.")
    with (OUT/"threat-geometry.json").open("x") as f:json.dump(receipt,f,indent=1,sort_keys=True);f.write("\n")
    print(json.dumps({k:v for k,v in receipt.items() if k!="rows"}))


if __name__=="__main__":main()
