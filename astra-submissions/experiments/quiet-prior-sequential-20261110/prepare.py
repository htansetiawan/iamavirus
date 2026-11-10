"""Freeze a source-validated, frontend-compatible sequential development panel."""
from datetime import datetime, timezone
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
OUT = ROOT / 'astra-submissions/analysis/quiet-prior-sequential-20261110'
BUILD = HERE / 'build'
NATIVE = HERE.parent / 'native-quiet-prior-20261110'
NB = NATIVE / 'build'
BASE = HERE.parent / 'guard-controls-20261109/build/pilot/extracted/iamavirus-v38-mist-c-allchildren'
OLD = HERE.parent / 'capture-fixed-prior-20261110'
CONFIRMED = ROOT / 'astra-submissions/analysis/prospective-full-prior-20261110b'
REF = ROOT.parent / 'fow-starter/referee.py'
TEAMS = ('Instructors', 'duck', 'HYPOTHERMIA', 'Greek Gift', 'Knight Vision', 'Strongly Invisible')
SEEDS = (0x6d6973742d63, 0x6d6973742d63 ^ 0x9e3779b97f4a7c15)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    with Path(p).open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
def encoded(move):
    sq = lambda s: ord(s[0]) - 97 + 8 * (int(s[1]) - 1)
    return sq(move[:2]) | (sq(move[2:4]) << 6) | (('pnbrqk'.index(move[4]) if len(move) == 5 else 6) << 12)


class MoveList(ctypes.Structure):
    _fields_ = [('moves', ctypes.c_uint16 * 256), ('count', ctypes.c_int)]


def load_ref():
    spec = importlib.util.spec_from_file_location('sequential_ref', REF)
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    return ref


def inspect_game(ref, frontend, replay, us):
    board = ref.FowBoard(); frames = replay['frames']
    initial = (0, 7) if us == 0 else (56, 63)
    rights = sum(1 << s for s in initial)
    rook = 'R' if us == 0 else 'r'; king = 'K' if us == 0 else 'k'
    previous_view = None; unsupported = []
    lines = [f"game {replay['id']} {us}"]
    for ply, frame in enumerate(frames):
        assert frame['ply'] == ply
        if ply:
            text = frame['move']; move = ref.chess.Move.from_uci(text)
            assert move in ref.fow_moves(board)
            if (ply - 1) % 2 == us:
                # Only our known past actions/view update our castling ledger.
                if previous_view[move.from_square] == king: rights = 0
                rights &= ~(1 << move.from_square)
            board.push(move)
        values = [''.join(board.piece_at(s).symbol() if board.piece_at(s) else '-' for s in range(64)),
                  ref.observation(board, True), ref.observation(board, False)]
        assert values == [frame[k] for k in ('board', 'white', 'black')]
        view = values[1 + us]
        for square in initial:
            if view[square] != rook: rights &= ~(1 << square)
        if king not in view: rights = 0
        # Gold metadata checks this private ledger, never supplies its input.
        assert rights == board.castling_rights & sum(1 << s for s in initial)
        if ply < len(frames) - 1 and ply % 2 == us:
            moves = MoveList(); frontend.view_moves(view.encode(), us, rights, ctypes.byref(moves))
            actual = frames[ply + 1]['move']
            if encoded(actual) not in moves.moves[:moves.count]: unsupported.append(dict(ply=ply, action=actual))
        if 0 < ply < len(frames) - 1:
            own = (ply - 1) % 2 == us
            upcoming = frames[ply + 1]['move'] if ply % 2 == us else '-'
            ep = -1 if board.ep_square is None else board.ep_square
            lines.append(f"{'us' if own else 'them'} {frame['move'] if own else '-'} {view} {values[0]} {ply % 2} {board.castling_rights:x} {ep} {board.halfmove_clock} {upcoming}")
        previous_view = view
    return lines, unsupported, len(frames)


def main():
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    assert json.loads((ROOT / 'astra-submissions/analysis/native-quiet-prior-20261110/check-result.json').read_text())['passed']
    cohort = json.loads((CONFIRMED / 'cohort.json').read_text()); archive = Path(cohort['source_archive'])
    ref = load_ref()
    frontend = ctypes.CDLL(str(NB / 'adapter.so')); frontend.fow_init()
    frontend.view_moves.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint64, ctypes.POINTER(MoveList)]
    # Copy literal deployed guard predicates, including their known exchange
    # approximation/promotion limit. This evaluates that predicate, not an
    # exact actual material-loss or terminal-outcome probability.
    main_source = (BASE / 'src/main.c').read_text()
    parts = [next(line for line in main_source.splitlines() if line.startswith('static const int piece_pawns')) + '\n']
    for name in ('queen_risks', 'king_risks'):
        start = main_source.index('static void ' + name + '(')
        end = main_source.index('\n}\n', start) + 3
        parts.append(main_source[start:end])
    (BUILD / 'guard_predicates.h').write_text('\n'.join(parts))
    groups = {}; considered = []; used = set(); total_frames = 0
    for team in TEAMS:
        candidates = sorted([g for g in cohort['games'] if team in (g['white'], g['black'])],
                            key=lambda g: hashlib.sha256(('native-sequential323:' + team + ':' + g['game']).encode()).digest())
        chosen = []
        for game in candidates:
            if game['game'] in used: continue
            sides = [s for s in (0, 1) if game[('white', 'black')[s]] == team]
            if len(sides) != 1: continue
            us = sides[0] ^ 1
            raw = archive / 'games' / game['game'] / 'replay.json'
            assert sha(raw) == game['replay_sha256']
            replay = json.loads(raw.read_text()); assert replay['id'] == game['game'] and replay.get('rulesVersion') == 'fow-v1'
            lines, unsupported, frames = inspect_game(ref, frontend, replay, us)
            considered.append(dict(game=game['game'], team=team, observer=us, raw_path=str(raw), replay_sha256=sha(raw),
                                   frontend_compatible=not unsupported, unsupported_actions=unsupported, course_frames=frames))
            if unsupported: continue
            path = OUT / (game['game'] + '.trace'); path.write_text('\n'.join(lines) + '\n')
            chosen.append(dict(game=game['game'], team=team, observer=us, our_name=game[('white', 'black')[us]],
                               created_at=game['created_at'], trace=str(path), trace_sha256=sha(path),
                               replay_path=str(raw), replay_sha256=sha(raw), frames=frames, rows=len(lines) - 1))
            used.add(game['game']); total_frames += frames
            if len(chosen) == 8: break
        assert len(chosen) == 8, (team, len(chosen))
        groups[team] = chosen
    games = [groups[team][i] for i in range(8) for team in TEAMS]
    save(OUT / 'source-selection.json', dict(considered=considered, selected=games,
         scope='Source/rules/frontend eligibility only, no belief update, model score or outcome-based selection.'))
    flags = ['gcc', '-O2', '-std=c11', '-pthread', '-D_POSIX_C_SOURCE=199309L']
    commands = []
    for arm in ('original', 'adapter'):
        src = NB / arm
        commands.append(flags + ['-I' + str(src), '-I' + str(BUILD), '-I' + str(NATIVE), '-I' + str(OLD),
                                 str(HERE / 'trace.c'), *[str(src / n) for n in ('board.c', 'belief.c', 'movemodel.c')],
                                 '-lm', '-o', str(BUILD / ('trace-' + arm))])
    commands.append(flags + ['-I' + str(NB / 'original'), '-I' + str(BUILD), str(HERE / 'guard_unit.c'),
                             str(NB / 'original/board.c'), '-lm', '-o', str(BUILD / 'guard-unit')])
    builds = []
    for command in commands:
        r = subprocess.run(command, capture_output=True, text=True, timeout=60)
        builds.append(dict(command=command, code=r.returncode, stdout=r.stdout, stderr=r.stderr))
        assert r.returncode == 0, r.stderr
    r = subprocess.run([str(BUILD / 'guard-unit')], capture_output=True, text=True, timeout=20)
    assert r.returncode == 0, r.stderr
    save(OUT / 'preparation.json', dict(at=datetime.now(timezone.utc).isoformat(), builds=builds,
                                      guard_unit=json.loads(r.stdout), selected_course_frames=total_frames,
                                      considered_games=len(considered), frontend_exclusions=sum(not c['frontend_compatible'] for c in considered)))
    print(json.dumps(dict(games=len(games), frames=total_frames, considered=len(considered),
                          unsupported=sum(not c['frontend_compatible'] for c in considered), build_count=len(builds))), flush=True)


if __name__ == '__main__': main()
