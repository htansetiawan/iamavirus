"""Explicit original erf/math teacher function, with unchanged checkpoint keys.

Offline reference only. Bypasses fused module inference without changing the
process-wide MHA flag; no fitting, candidate mixing, identity or target input.
"""
import torch
from torch import nn
from torch.nn import functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel


def attention(layer, query, key, value):
    """Functional MHA bypasses _native_multi_head_attention dispatch."""
    assert layer.batch_first and layer._qkv_same_embed_dim
    assert layer.dropout == 0 and layer.bias_k is None and layer.bias_v is None
    assert not layer.add_zero_attn
    # Preserve tensor identity for the same packed QKV/KV projection that the
    # original training path uses, rather than three unrelated GEMMs.
    if query is key is value:
        query = key = value = query.transpose(0, 1)
    elif key is value:
        query = query.transpose(0, 1); key = value = key.transpose(0, 1)
    else:
        query, key, value = (v.transpose(0, 1) for v in (query, key, value))
    output, _ = F.multi_head_attention_forward(query, key, value,
        layer.embed_dim, layer.num_heads, layer.in_proj_weight, layer.in_proj_bias,
        layer.bias_k, layer.bias_v, layer.add_zero_attn, 0.,
        layer.out_proj.weight, layer.out_proj.bias, training=False,
        need_weights=False)
    return output.transpose(0, 1)


def encoder(layer, x):
    assert isinstance(layer, nn.TransformerEncoderLayer) and layer.norm_first
    assert layer.activation is F.gelu
    assert all(getattr(layer, name).p == 0 for name in ('dropout', 'dropout1', 'dropout2'))
    normalized = layer.norm1(x)
    x = x + attention(layer.self_attn, normalized, normalized, normalized)
    # Original activation='gelu' is erf GELU; spell it out to avoid the fused
    # CUDA encoder's tanh approximation observed in324.
    return x + layer.linear2(F.gelu(layer.linear1(layer.norm2(x)), approximate='none'))


@torch.no_grad()
def forward(model, piece, visibility, castle, ep, halfmove, side, moves, features):
    """Same 319 architecture/weights, explicit original inference operations.

    Highest precision is a caller contract; this function neither toggles MHA
    global settings nor mutates weights. Its scoped SDPA selection restores on
    return, including exceptions. This is not a fast native runtime adapter.
    """
    assert not model.training, 'reference inference requires eval mode'
    assert torch.get_float32_matmul_precision() == 'highest'
    assert not torch.is_autocast_enabled() and not torch.is_autocast_enabled('cpu')
    with sdpa_kernel(SDPBackend.MATH):
        tokens = model.piece(piece) + model.square(torch.arange(64, device=piece.device))[None]
        tokens = tokens + model.visibility(visibility) + model.castle(castle)
        tokens = tokens + model.en_passant(ep) + model.side(side)[:, None]
        tokens = tokens + model.halfmove(halfmove[:, None].clamp(0, 100) / 100)[:, None]
        tokens = encoder(model.board_attention, tokens)
        queries = model.latent_queries[None].expand(len(piece), -1, -1)
        pooled = attention(model.latent_cross, queries, tokens, tokens)
        latents = model.latent_norm(queries + pooled)
        for block in model.latent_attention:
            latents = encoder(block, latents)
        source = (moves & 63)[..., None].expand(-1, -1, model.width)
        destination = ((moves >> 6) & 63)[..., None].expand(-1, -1, model.width)
        query = model.source(tokens.gather(1, source))
        query = query + model.destination(tokens.gather(1, destination))
        query = query + model.promotion(moves >> 12) + model.features(features)
        query = model.query_norm(query)
        context = attention(model.move_cross, query, latents, latents)
        return model.head(query + context).squeeze(-1)
