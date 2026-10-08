"""Observation-only attention encoders and a task-trained residual bottleneck.

The public observe/score interface, GRU and four heads match learning.model.
The compressed variant borrows space-to-channel residual autoencoding from
DC-AE; it is not a reproduction of the image model or its compression claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import torch
from torch import nn
from torch.nn import functional as F

from learning.features import NUM_PLANES, NUM_SCALARS
from learning.model import ARCHITECTURE, CHANNELS, HIDDEN, FogPolicy


@dataclass(frozen=True)
class ModelConfig:
    variant: str = "cnn"
    attention_blocks: int = 2
    attention_heads: int = 4
    latent_channels: int = 32
    attention_channels: int = CHANNELS

    def validate(self):
        if self.variant not in ("cnn", "attention", "compressed_attention"):
            raise ValueError(f"unknown variant {self.variant!r}")
        if self.attention_blocks < 1 or self.attention_heads < 1:
            raise ValueError("attention blocks/heads must be positive")
        if self.attention_channels < 1 or self.attention_channels % self.attention_heads:
            raise ValueError("attention heads must divide the positive encoder width")
        if self.latent_channels < 1 or (4 * CHANNELS) % self.latent_channels:
            raise ValueError("latent channels must be a positive divisor of 256")

    @property
    def architecture(self):
        if self.variant == "cnn":
            return ARCHITECTURE
        stem = f"astra-attn{self.attention_channels}x{self.attention_blocks}h{self.attention_heads}"
        if self.variant == "compressed_attention":
            stem += f"-residual-latent{self.latent_channels}x4x4"
        return stem + "-gru256-heads-v1"


def geometry_features():
    """Public square geometry only, never occupancy or privileged attacks."""
    sq = torch.arange(64)
    x, y = sq % 8, sq // 8
    dx, dy = x[:, None] - x[None, :], y[:, None] - y[None, :]
    ax, ay = dx.abs(), dy.abs()
    knight = ((ax == 1) & (ay == 2)) | ((ax == 2) & (ay == 1))
    return torch.stack([
        dx / 7, dy / 7, ax / 7, ay / 7,
        (dx == 0).float(), (dy == 0).float(), (ax == ay).float(),
        knight.float(), torch.eye(64),
    ])


class SquareAttention(nn.Module):
    """Pre-norm attention, explicit matmuls for stable CPU ONNX export."""
    def __init__(self, heads=4, channels=CHANNELS):
        super().__init__()
        self.heads, self.head_width, self.channels = heads, channels // heads, channels
        self.norm1 = nn.LayerNorm(channels)
        self.qkv = nn.Linear(channels, channels * 3)
        self.out = nn.Linear(channels, channels)
        self.norm2 = nn.LayerNorm(channels)
        self.ff1 = nn.Linear(channels, channels * 2)
        self.ff2 = nn.Linear(channels * 2, channels)
        self.register_buffer("geometry", geometry_features().flatten(1))
        self.geometry_weights = nn.Parameter(torch.zeros(heads, 9))

    def forward(self, x):
        batch = x.shape[0]
        qkv = self.qkv(self.norm1(x)).reshape(batch, 64, 3, self.heads, self.head_width)
        q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        bias = (self.geometry_weights @ self.geometry).reshape(self.heads, 64, 64)
        attention = torch.softmax((q @ k.transpose(-2, -1)) * (self.head_width ** -0.5) + bias, dim=-1)
        update = (attention @ v).transpose(1, 2).reshape(batch, 64, self.channels)
        x = x + self.out(update)
        return x + self.ff2(F.gelu(self.ff1(self.norm2(x))))


class ResidualBottleneck(nn.Module):
    """64x8x8 -> latent_channels x4x4 -> 64x8x8, without a bypass.

    Pixel unshuffle is lossless; grouped channel averaging is lossy. Learned
    residual projections can preserve task information beyond that fixed base.
    The decoded map supplies all per-square output heads. The GRU projection
    sees only the latent and public scalars, plus its existing recurrent state.
    """
    def __init__(self, latent_channels=32):
        super().__init__()
        if latent_channels < 1 or (CHANNELS * 4) % latent_channels:
            raise ValueError("latent channels must divide 256")
        self.latent_channels = latent_channels
        self.group = CHANNELS * 4 // latent_channels
        self.encode_residual = nn.Conv2d(CHANNELS * 4, latent_channels, 1)
        self.decode_residual = nn.Conv2d(latent_channels, CHANNELS * 4, 1)
        for layer in (self.encode_residual, self.decode_residual):
            nn.init.zeros_(layer.weight)
            nn.init.zeros_(layer.bias)

    def encode(self, spatial):
        rearranged = F.pixel_unshuffle(spatial, 2)
        base = rearranged.reshape(-1, self.latent_channels, self.group, 4, 4).mean(2)
        return base + self.encode_residual(rearranged)

    def decode(self, latent):
        base = latent.unsqueeze(2).expand(-1, -1, self.group, -1, -1).reshape(-1, CHANNELS * 4, 4, 4)
        return F.pixel_shuffle(base + self.decode_residual(latent), 2)

    def forward(self, spatial):
        latent = self.encode(spatial)
        return latent, self.decode(latent)


class AttentionFogPolicy(FogPolicy):
    def __init__(self, config: ModelConfig):
        config.validate()
        if config.variant == "cnn":
            raise ValueError("use FogPolicy for the unchanged CNN control")
        super().__init__()
        self.config = config
        # Delete the CNN rather than carrying unused trainable parameters.
        del self.stem, self.blocks
        width = config.attention_channels
        self.token_embed = nn.Linear(NUM_PLANES, width)
        self.position = nn.Parameter(torch.empty(1, 64, width))
        nn.init.normal_(self.position, std=0.02)
        self.attention = nn.ModuleList([SquareAttention(config.attention_heads, width)
                                        for _ in range(config.attention_blocks)])
        self.final_norm = nn.LayerNorm(width)
        # Keep the same 64-channel output / 256-state runtime ABI. The teacher
        # can have a larger internal encoder without changing legal-move heads.
        # Identity preserves every existing 64-wide checkpoint parameter key.
        self.spatial_adapter = nn.Identity() if width == CHANNELS else nn.Linear(width, CHANNELS)
        self.bottleneck = None
        if config.variant == "compressed_attention":
            self.bottleneck = ResidualBottleneck(config.latent_channels)
            self.project = nn.Linear(config.latent_channels * 16 + NUM_SCALARS, HIDDEN)

    def encode(self, planes):
        tokens = self.token_embed(planes.flatten(2).transpose(1, 2)) + self.position
        for block in self.attention:
            tokens = block(tokens)
        spatial = self.spatial_adapter(self.final_norm(tokens)).transpose(1, 2).reshape(-1, CHANNELS, 8, 8)
        if self.bottleneck is None:
            return spatial.flatten(1), spatial
        latent, decoded = self.bottleneck(spatial)
        return latent.flatten(1), decoded

    def observe(self, planes, scalars, hidden):
        encoded, spatial = self.encode(planes)
        inp = F.relu(self.project(torch.cat([encoded, scalars], dim=1)))
        next_hidden = self.gru(inp, hidden)
        value = torch.tanh(self.value2(F.relu(self.value1(next_hidden))))
        per_square = spatial.flatten(2).transpose(1, 2)
        h = next_hidden.unsqueeze(1).expand(-1, 64, -1)
        belief = self.belief2(F.relu(self.belief1(torch.cat([per_square, h], dim=2))))
        return next_hidden, spatial, belief, value


def make_model(config: ModelConfig):
    config.validate()
    return FogPolicy() if config.variant == "cnn" else AttentionFogPolicy(config)


def model_metadata(config: ModelConfig):
    return {"model_config": asdict(config), "architecture": config.architecture,
            "input_boundary": "actor observations, own actions/history, public scalars only",
            "runtime_interface": "observe[B,32,8,8;B,8;B,256], score[B,M]",
            "bottleneck_elements": config.latent_channels * 16 if config.variant == "compressed_attention" else 4096}
