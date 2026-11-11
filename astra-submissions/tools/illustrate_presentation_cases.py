"""Generate explanatory SVGs from already-audited immutable replay fixtures.

No bot, fit, search or new experimental condition is run. Hidden squares are
drawn from each recorded private view, never reconstructed from truth.
"""
from datetime import datetime, timezone
from html import escape
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/assets'
NAMES = dict(P='pawn', N='knight', B='bishop', R='rook', Q='queen', K='king')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def square(name):
    return ord(name[0]) - ord('a') + 8 * (int(name[1]) - 1)


def center(index, x, y):
    return x + 32 * (index % 8) + 16, y + 32 * (7 - index // 8) + 16


def figure(title, description, frame, panels, action, attacker, destination):
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 936 382" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
             '<rect width="936" height="382" rx="12" fill="#fff"/>',
             '<style>text{font-family:Inter,Arial,sans-serif;fill:#373737}.sq{font-size:11px;fill:#777}.piece{font-size:18px;font-weight:600;text-anchor:middle;dominant-baseline:central}</style>',
             '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#99613b"/></marker></defs>',
             f'<text x="24" y="28" font-size="17" font-weight="600">{escape(title)}</text>']
    for panel, (label, key) in enumerate(panels):
        x, y = panel * 312 + 35, 77
        board = frame[key]
        assert len(board) == 64
        parts.append(f'<text x="{x}" y="58" font-size="13">{escape(label)}</text>')
        for index, piece in enumerate(board):
            cx, cy = center(index, x, y)
            location = chr(ord('a') + index % 8) + str(index // 8 + 1)
            shade = '#e8e8e8' if piece == '?' else ('#f2f1ef' if (index % 8 + index // 8) % 2 == 0 else '#fcfcfb')
            piece_label = 'hidden' if piece == '?' else 'empty' if piece == '-' else ('White ' if piece.isupper() else 'Black ') + NAMES[piece.upper()]
            parts.append(f'<g><title>{location}: {piece_label}</title><rect x="{cx-16}" y="{cy-16}" width="32" height="32" fill="{shade}"/>')
            if piece == '?':
                parts.append(f'<text x="{cx}" y="{cy}" class="piece" opacity=".45">?</text>')
            elif piece != '-':
                fill, ink = ('#fff', '#333') if piece.isupper() else ('#454545', '#fff')
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{fill}" stroke="#737373" stroke-width=".8"/>')
                parts.append(f'<text x="{cx}" y="{cy}" class="piece" style="fill:{ink}">{piece.upper()}</text>')
            parts.append('</g>')
        for file in range(8):
            parts.append(f'<text x="{x+32*file+16}" y="{y+273}" class="sq" text-anchor="middle">{chr(97+file)}</text>')
        for rank in range(8):
            parts.append(f'<text x="{x-10}" y="{y+32*rank+20}" class="sq">{8-rank}</text>')
        # Actual recorded move is an annotation, not an inferred intent.
        ax, ay = center(square(action[:2]), x, y)
        bx, by = center(square(action[2:4]), x, y)
        parts.append(f'<path d="M{ax},{ay} L{bx},{by}" stroke="#99613b" stroke-width="2.5" opacity=".85" marker-end="url(#arrow)"/>')
        source = square(attacker)
        # Never draw an unseen attacker's identity/line on a private-view panel.
        if key == 'board' or board[source] not in ('?', '-'):
            ax, ay = center(source, x, y)
            bx, by = center(square(destination), x, y)
            parts.append(f'<path d="M{ax},{ay} L{bx},{by}" stroke="#785f94" stroke-width="2" stroke-dasharray="4 3" opacity=".8"/>')
    parts.append('<text x="35" y="368" font-size="11">Light circles: White pieces · Dark circles: Black pieces · ? hidden · Solid: actual move · Dotted: attacker line when visible</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main():
    positive_result = ROOT / 'astra-submissions/analysis/v38-mist-positive-20261111/result.json'
    positive = read(positive_result)
    selected = next(r for r in positive['records'] if r['id'] == 'c8ozqj0m')
    win_path = ROOT / 'data/astra-spool/v38-mist-wins-20261111/c8ozqj0m.json'
    assert sha(win_path) == selected['replay_sha256']
    win = read(win_path)
    assert win['whiteVersion'] == 38 and win['blackVersion'] == 2 and win['result'] == '1-0'
    before_win = win['frames'][33]
    assert before_win['move'] == 'g5g7' and win['frames'][34]['move'] == 'g8g7'
    assert before_win['board'][square('g4')] == 'Q' and before_win['black'][square('g4')] == '?'
    assert before_win['black'][square('g7')] == 'R'
    loss_path = ROOT / 'data/astra-spool/compact-mass-playing-20261111/jobs/mass-p2-black/replay.json'
    receipt = read(loss_path.parent / 'result.json')
    assert sha(loss_path) == receipt['replay_sha256']
    loss = read(loss_path)
    assert receipt['score'] == 0 and loss['result'] == '1-0'
    before_loss = loss['frames'][115]
    assert loss['frames'][116]['move'] == 'f4f3'
    assert before_loss['board'][square('e2')] == 'K' and before_loss['black'][square('e2')] == '?'
    last_log = next(line for line in reversed(loss['privateDiagnostics']['black'].splitlines()) if line.startswith('mist: n='))
    assert re.search(r'n=58 \|P\|=6\(capped\) samples=6 moves=24', last_log)
    diagnosis_path = ROOT / 'astra-submissions/analysis/onpolicy-prior-diagnosis-20261111/result.json'
    diagnosis = read(diagnosis_path)
    row = next(r for r in diagnosis['records'] if r['game'] == 'mass-p2-black')
    final = row['final_decision']['learned']
    assert final['worlds'] == 6 and final['matches'] == 1 and final['king_label'] == 1
    assert final['kingt'] == final['truth_share']
    illustrations = [
        ('presentation-hidden-support.svg', figure('v38 win: the rook is visible, its queen support is hidden',
          'After White Rg7, Black can see the offered rook but not White Qg4. Black captures with Kg8g7 and loses to the hidden queen line. Kh8 was an immediate surviving reply.',
          before_win, [('True board — replay only', 'board'), ('IAmAVirus sees — White', 'white'), ('Mist sees — Black', 'black')], 'g8g7', 'g4', 'g7')),
        ('presentation-six-world-loss.svg', figure('Experimental loss: six worlds searched, danger underweighted',
          'Before Black Kf4f3, White Ke2 is hidden from Black. The destination f3 is visibly empty but attacked by the unseen king. Black moves there and loses despite a nine-point material lead.',
          before_loss, [('True board — replay only', 'board'), ('Candidate sees — Black', 'black'), ('v38 sees — White', 'white')], 'f4f3', 'e2', 'f3')),
    ]
    OUTPUT.mkdir(exist_ok=True)
    for name, text in illustrations:
        path = OUTPUT / name
        with path.open('x') as stream:
            stream.write(text)
    report = dict(at=datetime.now(timezone.utc).isoformat(), source_sha256={str(p.relative_to(ROOT)): sha(p) for p in
        (Path(__file__), positive_result, win_path, loss_path, loss_path.parent / 'result.json', diagnosis_path)},
        figures={name: sha(OUTPUT / name) for name, _ in illustrations},
        win=dict(game=win['id'], frame=33, ply=34, move='g8g7', visible_bait='g7', hidden_attacker='g4',
                 surviving_reply=selected['ending']['safe_moves'], labels_from='existing 356 course/C++ audit'),
        loss=dict(game='mass-p2-black', frame=115, ply=116, move='f4f3', hidden_attacker='e2',
                  candidate_search_log=last_log, reconstructed_fatal_mass=final['kingt'],
                  reconstructed_truth_share=final['truth_share'],
                  labels_from='existing 357/360 course/C++/fixed-history audits'),
        scope='Illustration of two already-audited selected fixtures. Public snapshots only; no full raw export, '
              'new model, bot invocation, game, performance estimate or counterfactual policy. '
              'Private panels use recorded observations; unseen attacker lines omitted from them. '
              'The loss is an experimental candidate, not arena-v38.')
    path = ROOT / 'astra-submissions/analysis/presentation-audit-20261111/case-illustrations.json'
    with path.open('x') as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(figures=report['figures'], loss_log=last_log), indent=2))


if __name__ == '__main__':
    main()
