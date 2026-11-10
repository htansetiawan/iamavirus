"""Additional post-collection check of every text-input field, including history."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'astra-submissions/analysis/root-strata-20261110'
POP = ROOT/'astra-submissions/analysis/root-population-20261110/case/population.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pop = json.loads(POP.read_text())
    lines = (OUT/'population.txt').read_text().splitlines()
    assert list(map(int, lines[0].split())) == [pop['count'], pop['us'], 32, len(pop['moves'])]
    assert len(lines) == 1+len(pop['moves'])+pop['count']
    for line, move in zip(lines[1:], pop['moves']):
        uci, kept = line.split()
        assert uci == move['uci'] and int(kept) == int(move['base_kept'])
    for line, world in zip(lines[1+len(pop['moves']):], pop['worlds']):
        board, side, castle, ep, halfmove, history, logw = line.split()
        assert board == world['board'] and int(side) == world['side']
        assert int(castle, 16) == int(world['castle'], 16)
        assert int(ep) == world['ep'] and int(halfmove) == world['halfmove']
        assert int(history, 16) == int(world['hist'], 16)
        assert struct.pack('f', float(logw)) == struct.pack('f', world['logw'])
    report = dict(at=datetime.now(timezone.utc).isoformat(), passed=True, verified_worlds=pop['count'],
                  input_sha256=sha(OUT/'population.txt'), population_sha256=sha(POP), auditor_sha256=sha(Path(__file__)),
                  scope='Post-collection extra verification. Exact input mapping, float weights, rule metadata, '
                        'opponent history hashes and original guard mask; no new actor or search.')
    with (OUT/'input-audit.json').open('x') as handle:
        json.dump(report, handle, indent=2); handle.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
