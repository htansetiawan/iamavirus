"""Read-only audit of the current SunTzu data splits and hierarchy contract.

No torch import, GPU use, training, or changes to Fable's implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pairs', type=Path, default=Path('data/suntzu2/pairs-v1.npz'))
    ap.add_argument('--raw', type=Path, default=Path('data/raw'))
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    with np.load(args.pairs, allow_pickle=False) as d:
        gid, opp, white, ply = (d[k] for k in ('gid', 'opp', 'white', 'ply'))
        danger, opportunity = d['danger'], d['opportunity']
    ug, inverse = np.unique(gid, return_inverse=True)
    tokenizer_test = set(np.random.default_rng(0).choice(ug, len(ug) // 10, replace=False))
    eligible = (opp >= 0) & (opp < 12)
    strategy_games = np.unique(gid[eligible])
    strategy_test = set(np.random.default_rng(0).choice(strategy_games, len(strategy_games) // 5, replace=False))
    tokenizer_train = set(ug) - tokenizer_test
    counts = np.bincount(inverse[eligible] * 2 + white[eligible], minlength=2 * len(ug))
    counts = counts[counts > 0]
    lengths = np.minimum(counts, 60)
    terminal_ply = np.full(len(ug), -1, dtype=np.int32)
    missing = []
    for index, game in enumerate(ug):
        path = args.raw / 'games' / str(game) / 'listing.json'
        if not path.exists():
            missing.append(str(game))
            continue
        meta = json.loads(path.read_text())
        if meta.get('reason') == 'King capturable':
            terminal_ply[index] = meta['plies']
    terminal = eligible & (ply == terminal_ply[inverse])
    # Match the existing argsort/ordinal-rank AUC on an all-tied example.
    scores = np.zeros(4)
    labels = np.array([0, 0, 1, 1], dtype=bool)
    ranks = np.empty(4)
    ranks[np.argsort(scores)] = np.arange(4)
    old_auc = (ranks[labels].sum() - 1) / 4
    assert old_auc != .5, 'Recheck tie ordering on this numpy version'
    report = {
        'pairs_file': str(args.pairs),
        'pairs_sha256': hashlib.sha256(args.pairs.read_bytes()).hexdigest(),
        'rows': len(gid), 'games': len(ug),
        'strategy_test_games': len(strategy_test),
        'strategy_test_seen_in_tokenizer_training': len(strategy_test & tokenizer_train),
        'strategy_test_unseen_in_tokenizer_training': len(strategy_test & tokenizer_test),
        'strategy_groups': len(counts),
        'valid_positions_with_maxlen60': int(lengths.sum()),
        'padded_positions_with_maxlen60': int(60 * len(lengths) - lengths.sum()),
        'padded_fraction': float(1 - lengths.sum() / (60 * len(lengths))),
        'terminal_opponent_events_in_strategy_source': int(terminal.sum()),
        'terminal_events_with_positive_opportunity': int((terminal & (opportunity == 1)).sum()),
        'positive_opportunity_events_in_strategy_source': int((eligible & (opportunity == 1)).sum()),
        'positive_danger_events_in_strategy_source': int((eligible & (danger == 1)).sum()),
        'terminal_events_kept_in_first60': int((terminal & (ply <= (119 + white))).sum()),
        'missing_listings': missing,
        'auc_tie_probe': {'scores': scores.tolist(), 'labels': labels.astype(int).tolist(),
                          'current_ordinal_auc': float(old_auc), 'correct_tie_aware_auc': .5},
        'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in map(Path, ['learning/suntzu2/extract.py',
                                              'learning/suntzu2/tokenizer.py',
                                              'learning/suntzu2/strategy.py'])},
        'interpretation': [
            'Overlapping unsupervised tokenizer training makes the downstream split transductive; it is not a fully held-out pipeline test.',
            'RVQ.forward currently computes MSE over padded positions; supervised heads alone use the valid mask.',
            'Terminal rows are valid for retrospective representation learning, but must be excluded from future-opportunity evaluation at actionable decision states.',
            'The current rank AUC does not average tied ranks. Quantized scores can tie often.',
            'Two RVQ residual books at one timescale do not by themselves implement a move/sequence/strategy control hierarchy.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_sha256', 'interpretation', 'missing_listings')}, indent=2))


if __name__ == '__main__':
    main()
