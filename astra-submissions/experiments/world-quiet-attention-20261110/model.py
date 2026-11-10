"""Unfitted full-world prior prototype; not an actor policy or leaf evaluator.

Capture-preserving normalization is reused from293. Latent query compression
is a standard architecture, already used for a different target in271.
"""
import torch
from torch import nn


def quiet_logp(base, residual, valid, capture, counts, history_total):
    """Change only within-quiet odds, then apply the unchanged native blend.

    Every row has a valid first candidate. Invalid entries may be padded;
    counts/total are the original native history counts, not fitted inputs.
    When total > sum(counts), the native mixture need not sum to one over
    this hypothetical world's available actions; preserve that behavior.
    """
    baseline = base.masked_fill(~valid, -torch.inf).log_softmax(-1)
    quiet = valid & ~capture
    safe = quiet.clone()
    safe[~quiet.any(-1), 0] = True
    old = base.masked_fill(~safe, -torch.inf).logsumexp(-1, keepdim=True)
    new = (base + residual).masked_fill(~safe, -torch.inf).logsumexp(-1, keepdim=True)
    use = quiet & (quiet.sum(-1, keepdim=True) > 1)
    # Match293's operation order exactly, including its zero residual identity.
    conditional = torch.where(use, baseline + residual + (old - new), baseline)
    safe_conditional = conditional.masked_fill(~valid, 0)
    log_count = torch.where(valid, counts.log(), torch.zeros_like(counts))
    prior_strength = base.new_tensor(4.0)
    mixed = torch.logaddexp(log_count, safe_conditional + prior_strength.log())
    mixed = mixed - (history_total[:, None] + prior_strength).log()
    result = torch.where(history_total[:, None] >= 3, mixed, conditional)
    return result.masked_fill(~valid, -torch.inf)


class WorldQuietTeacher(nn.Module):
    """Encode one hypothetical parent once, then query each candidate separately.

    No player identity, actual target action, result, future frame or clock is
    an input. The complete parent and both visibility masks ARE inputs: this
    is intentionally privileged per-world belief-prior computation. It must
    not be substituted for an information-set-realizable opponent policy.
    """
    def __init__(self, width=128, latents=8):
        super().__init__()
        self.width = width
        self.piece = nn.Embedding(13, width)
        self.square = nn.Embedding(64, width)
        self.visibility = nn.Embedding(4, width)
        self.castle = nn.Embedding(2, width)
        self.en_passant = nn.Embedding(2, width)
        self.side = nn.Embedding(2, width)
        self.halfmove = nn.Linear(1, width, bias=False)
        block = lambda: nn.TransformerEncoderLayer(
            width, 4, 2 * width, dropout=0., activation='gelu',
            batch_first=True, norm_first=True)
        self.board_attention = block()
        self.latent_queries = nn.Parameter(torch.randn(latents, width) * .02)
        self.latent_cross = nn.MultiheadAttention(width, 4, dropout=0., batch_first=True)
        self.latent_norm = nn.LayerNorm(width)
        self.latent_attention = nn.Sequential(block(), block())
        self.source = nn.Linear(width, width, bias=False)
        self.destination = nn.Linear(width, width, bias=False)
        self.promotion = nn.Embedding(5, width)
        self.features = nn.Linear(26, width, bias=False)
        self.query_norm = nn.LayerNorm(width)
        self.move_cross = nn.MultiheadAttention(width, 4, dropout=0., batch_first=True)
        self.head = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, width // 2),
                                  nn.SiLU(), nn.Linear(width // 2, 1))
        # Identity initialization: fitting starts from the native prior.
        nn.init.zeros_(self.head[-1].weight)
        nn.init.zeros_(self.head[-1].bias)

    def encode_board(self, piece, visibility, castle, ep, halfmove, side):
        tokens = self.piece(piece) + self.square(torch.arange(64, device=piece.device))[None]
        tokens = tokens + self.visibility(visibility) + self.castle(castle)
        tokens = tokens + self.en_passant(ep) + self.side(side)[:, None]
        tokens = tokens + self.halfmove(halfmove[:, None].clamp(0, 100) / 100)[:, None]
        tokens = self.board_attention(tokens)
        queries = self.latent_queries[None].expand(len(piece), -1, -1)
        pooled, _ = self.latent_cross(queries, tokens, tokens, need_weights=False)
        latents = self.latent_attention(self.latent_norm(queries + pooled))
        return tokens, latents

    def score_moves(self, encoded, moves, features):
        tokens, latents = encoded
        source = (moves & 63)[..., None].expand(-1, -1, self.width)
        destination = ((moves >> 6) & 63)[..., None].expand(-1, -1, self.width)
        query = self.source(tokens.gather(1, source))
        query = query + self.destination(tokens.gather(1, destination))
        query = query + self.promotion(moves >> 12) + self.features(features)
        query = self.query_norm(query)
        context, _ = self.move_cross(query, latents, latents, need_weights=False)
        return self.head(query + context).squeeze(-1)

    def forward(self, piece, visibility, castle, ep, halfmove, side, moves, features):
        encoded = self.encode_board(piece, visibility, castle, ep, halfmove, side)
        return self.score_moves(encoded, moves, features)
