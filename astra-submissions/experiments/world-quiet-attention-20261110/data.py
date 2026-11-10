"""Batch-local padding from318's ragged original TRAIN cache.

World fields and native features are privileged prior inputs. Metadata stays
on CPU for split/scoring only and is never passed to the network.
"""
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'astra-submissions/tools'))
from prior_training_cache import PriorCache
from reconstructed_cache import Cache

CONTEXT = np.dtype([('start', '<u8'), ('record', '<u4'), ('total', '<u4'),
                    ('target', '<u2'), ('count', '<u2'), ('game', '<u2'),
                    ('selection', 'u1'), ('flags', 'u1')])
FRAME = np.dtype([('board', 'u1', (32,)), ('white', '<u8'), ('black', '<u8'),
                  ('castle', '<u8'), ('ep', 'i1'), ('half', '<u2'), ('side', 'u1'),
                  ('action', '<u2'), ('selection', 'u1'), ('flags', 'u1')])
assert CONTEXT.itemsize == 24 and FRAME.itemsize == 64


class Dataset:
    def __init__(self, plan, device):
        self.device = torch.device(device)
        self.prior = PriorCache(plan['feature_cache'])
        self.world = Cache(plan['state_cache'])
        self.context = np.frombuffer(self.prior.contexts, dtype=CONTEXT)
        frames = np.frombuffer(self.world.data, dtype=FRAME)
        size = len(self.context)
        piece = np.empty((size, 64), np.uint8)
        visibility = np.empty_like(piece); castle = np.empty_like(piece); ep = np.empty_like(piece)
        half = np.empty(size, np.float32); side = np.empty(size, np.int64)
        self.meta = []
        squares = np.arange(64, dtype=np.uint64)
        for start in range(0, size, 4096):
            end = min(start + 4096, size)
            source = frames[self.context['record'][start:end]]
            packed = source['board']
            piece[start:end, 0::2] = packed & 15
            piece[start:end, 1::2] = packed >> 4
            visibility[start:end] = ((source['white'][:, None] >> squares) & 1) | (((source['black'][:, None] >> squares) & 1) << 1)
            castle[start:end] = (source['castle'][:, None] >> squares) & 1
            ep[start:end] = source['ep'][:, None] == np.arange(64)[None]
            half[start:end] = source['half']; side[start:end] = source['side']
        assert piece.max() <= 12
        self.board = [self.tensor(v) for v in (piece, visibility, castle, ep, half, side)]
        self.features = self.tensor(np.array(self.prior.rows['x'], copy=True))
        self.base = self.tensor(np.array(self.prior.rows['base'][:, 1], copy=True))
        self.counts = self.tensor(self.prior.rows['history'].astype(np.float32))
        self.moves = self.tensor(self.prior.rows['move'].astype(np.int64))
        self.starts = self.tensor(self.context['start'].astype(np.int64))
        self.length = self.tensor(self.context['count'].astype(np.int64))
        self.target = self.tensor(self.context['target'].astype(np.int64))
        self.total = self.tensor(self.context['total'].astype(np.float32))
        self.offsets = torch.arange(self.prior.manifest['max_width'], device=self.device)
        sets = {name: set(plan['split'][name]) for name in ('train', 'development')}
        assert not sets['train'] & sets['development']
        assert sets['train'] | sets['development'] == {g['game'] for g in self.world.games}
        self.indices = {'train': [], 'development': []}
        for i, context in enumerate(self.context):
            game = self.world.games[int(context['game'])]
            ply = int(context['record']) - game['start']
            source = frames[int(context['record'])]
            assert int(source['action']) == int(self.prior.rows[int(context['start']) + int(context['target'])]['move'])
            assert int(source['flags']) == int(context['flags'])
            assert ply in game['selected_plies'] and int(context['selection']) & 1
            flags = int(context['flags'])
            self.meta.append(dict(game=game['game'], ply=ply, team=game[('white', 'black')[ply % 2]],
                                  primary=ply // 2 >= 8 and not flags & 16,
                                  capture=bool(flags & 1), fatal=bool(flags & 16)))
            self.indices['train' if game['game'] in sets['train'] else 'development'].append(i)
        self.indices = {k: np.asarray(v, np.int64) for k, v in self.indices.items()}

    def tensor(self, array):
        return torch.from_numpy(np.ascontiguousarray(array)).to(self.device)

    def batch(self, indices):
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        length = self.length[indices, None]
        valid = self.offsets[None] < length
        # Duplicate the last actual candidate for padding, never cross into a
        # different row/game. The explicit valid mask removes these entries.
        positions = self.starts[indices, None] + torch.minimum(self.offsets[None], length - 1)
        x = self.features[positions]
        board = [v[indices].long() if i != 4 else v[indices] for i, v in enumerate(self.board)]
        return dict(x=x, base=self.base[positions], counts=self.counts[positions],
                    moves=self.moves[positions], capture=x[:, :, 0] > 0, valid=valid,
                    y=self.target[indices], history_n=self.total[indices], board=board)
