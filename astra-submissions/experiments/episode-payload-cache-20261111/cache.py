"""Content-addressed episode payload cache; isolated infrastructure prototype.

The caller supplies a replay-content SHA and a complete pipeline fingerprint.
Hits reuse that pinned input snapshot; they do not attest a mutable raw path.
Only small metadata is reserialized when the caller assigns a fold. Actor and
target bytes remain exact. This module neither exports nor publishes datasets.
"""
from dataclasses import asdict
import hashlib
import json
import re
import sqlite3
import struct
import zlib

HEADER = struct.Struct(">4sIIII")
MAGIC = b"EPC1"
MAX_RAW = 32 * 1024 * 1024
SPLITS = {"train", "validation", "test"}


class CorruptEntry(ValueError):
    pass


def checked_hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("expected a lowercase SHA-256")
    return value


def encoded(value):
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode()


def pack(episodes, source_sha):
    if len(episodes) != 2 or [ep.actor.side for ep in episodes] != [0, 1]:
        raise ValueError("one episode per color required")
    pieces = []
    for episode in episodes:
        meta = asdict(episode.metadata)
        if meta["source_hash"] != source_sha:
            raise ValueError("episode source identity differs from requested content")
        meta["split"] = ""
        prefix = b'{"actor":' + encoded(asdict(episode.actor))
        prefix += b',"targets":' + encoded(asdict(episode.targets)) + b',"metadata":'
        pieces.extend((prefix, encoded(meta)))
    payload = HEADER.pack(MAGIC, *(len(p) for p in pieces)) + b"".join(pieces)
    if len(payload) > MAX_RAW:
        raise ValueError("episode payload exceeds fixed cache cap")
    return payload


def unpack(payload, source_sha):
    if len(payload) < HEADER.size:
        raise CorruptEntry("short payload")
    magic, *lengths = HEADER.unpack_from(payload)
    if magic != MAGIC or sum(lengths) + HEADER.size != len(payload):
        raise CorruptEntry("bad payload framing")
    pieces, offset = [], HEADER.size
    for length in lengths:
        pieces.append(payload[offset:offset + length])
        offset += length
    pairs = []
    for prefix, meta_bytes in zip(pieces[::2], pieces[1::2], strict=True):
        try:
            meta = json.loads(meta_bytes)
        except (ValueError, UnicodeError) as exc:
            raise CorruptEntry("bad cached metadata") from exc
        if not isinstance(meta, dict) or meta.get("source_hash") != source_sha or meta.get("split") != "":
            raise CorruptEntry("cached metadata identity differs")
        pairs.append((prefix, meta))
    return pairs


class Cache:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("""CREATE TABLE IF NOT EXISTS episodes (
          pipeline_sha TEXT NOT NULL, source_sha TEXT NOT NULL,
          compressed_sha TEXT NOT NULL, raw_sha TEXT NOT NULL, payload BLOB NOT NULL,
          PRIMARY KEY (pipeline_sha, source_sha)) WITHOUT ROWID""")
        self.connection.commit()

    def close(self):
        self.connection.close()

    def get(self, pipeline_sha, source_sha):
        checked_hash(pipeline_sha)
        checked_hash(source_sha)
        row = self.connection.execute(
            "SELECT compressed_sha,raw_sha,payload FROM episodes WHERE pipeline_sha=? AND source_sha=?",
            (pipeline_sha, source_sha)).fetchone()
        if row is None:
            return None
        compressed_sha, raw_sha, blob = row
        if hashlib.sha256(blob).hexdigest() != compressed_sha:
            raise CorruptEntry("compressed payload hash differs")
        try:
            decoder = zlib.decompressobj()
            raw = decoder.decompress(blob, MAX_RAW + 1)
        except zlib.error as exc:
            raise CorruptEntry("payload decompression failed") from exc
        if len(raw) > MAX_RAW or decoder.unconsumed_tail or decoder.unused_data or not decoder.eof:
            raise CorruptEntry("payload cap, trailer or stream boundary differs")
        if hashlib.sha256(raw).hexdigest() != raw_sha:
            raise CorruptEntry("raw payload hash differs")
        return unpack(raw, source_sha)

    def render(self, pipeline_sha, source_sha, split, builder):
        if split not in SPLITS:
            raise ValueError("unknown split")
        pairs = self.get(pipeline_sha, source_sha)
        hit = pairs is not None
        if not hit:
            raw = pack(builder(), source_sha)
            blob = zlib.compress(raw, level=1)
            values = (pipeline_sha, source_sha, hashlib.sha256(blob).hexdigest(),
                      hashlib.sha256(raw).hexdigest(), blob)
            with self.connection:
                self.connection.execute("INSERT OR IGNORE INTO episodes VALUES (?,?,?,?,?)", values)
                stored = self.connection.execute(
                    "SELECT raw_sha FROM episodes WHERE pipeline_sha=? AND source_sha=?",
                    (pipeline_sha, source_sha)).fetchone()
                if stored[0] != values[3]:
                    raise CorruptEntry("same input key produced different canonical payloads")
            pairs = self.get(pipeline_sha, source_sha)
        lines = []
        for prefix, metadata in pairs:
            metadata["split"] = split
            lines.append(prefix + encoded(metadata) + b"}\n")
        return tuple(lines), hit
