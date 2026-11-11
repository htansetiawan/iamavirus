"""Explicit source-bound replay metadata corrections; never rewrite raw evidence."""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re

from .ingest import replay_hash

FORMAT = "iamavirus.metadata-overlay.v1"
FIELDS = frozenset({"createdAt", "white", "black", "whitePlayerId", "blackPlayerId",
                    "whiteVersion", "blackVersion"})
_STAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?(?:Z|[+-]\d\d:\d\d)")


def _is_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _check_metadata(metadata):
    if not isinstance(metadata, dict) or not metadata or set(metadata) - FIELDS:
        raise ValueError("overlay metadata must contain only supported metadata fields")
    for key, value in metadata.items():
        if key == "createdAt":
            if not isinstance(value, str) or not _STAMP.fullmatch(value):
                raise ValueError("overlay createdAt must be an RFC3339 timestamp")
            stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError("overlay createdAt must include a timezone")
        elif key in ("white", "black"):
            if not isinstance(value, str) or not value:
                raise ValueError(f"overlay {key} must be a nonempty name")
        elif key.endswith("PlayerId"):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"overlay {key} must be a nonempty ID or null")
        elif value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"overlay {key} must be a nonnegative integer or null")


class MetadataOverlay:
    def __init__(self, path: Path, digest: str, records: dict, payload: bytes):
        self.path, self.sha256, self.records = path, digest, records
        self._payload = payload

    def apply_rows(self, rows: list[dict]) -> tuple[list[dict], list[str]]:
        effective, applied = [], []
        for row in rows:
            game = row["id"]
            record = self.records.get(game)
            if record is None:
                effective.append(row)
                continue
            if row.get("moves_sha256") != record["moves_sha256"]:
                raise ValueError(f"metadata overlay journal move hash differs for {game}")
            effective.append({**row, **record["metadata"]})
            applied.append(game)
        return effective, applied

    def apply_replay(self, game: str, replay: dict, source_sha256: str) -> dict:
        record = self.records.get(game)
        if record is None:
            return replay
        if replay.get("id") != game or source_sha256 != record["original_sha256"]:
            raise ValueError(f"metadata overlay raw source differs for {game}")
        if replay_hash(replay) != record["moves_sha256"]:
            raise ValueError(f"metadata overlay replay move hash differs for {game}")
        return {**replay, **record["metadata"]}

    def write_snapshot(self, path: Path) -> None:
        with path.open("xb") as stream:
            stream.write(self._payload)
            stream.flush()
            os.fsync(stream.fileno())

    def manifest_info(self, applied: list[str], snapshot: Path) -> dict:
        return {"path": str(snapshot), "input_path": str(self.path),
                "sha256": self.sha256, "format": FORMAT,
                "records": len(self.records), "applied_games": len(applied),
                "unused_records": len(self.records) - len(applied)}


def load_metadata_overlay(path: Path) -> MetadataOverlay:
    path = Path(path).resolve()
    payload = path.read_bytes()
    data = json.loads(payload)
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("records"), list):
        raise ValueError("unsupported metadata overlay format")
    records = {}
    for record in data["records"]:
        if not isinstance(record, dict):
            raise ValueError("overlay records must be objects")
        game = record.get("id")
        if not isinstance(game, str) or not re.fullmatch(r"[a-z0-9]{8}", game):
            raise ValueError("overlay game IDs must be eight lowercase letters/digits")
        if game in records:
            raise ValueError(f"duplicate metadata overlay record {game}")
        for key in ("original_sha256", "moves_sha256", "response_sha256"):
            if not _is_hash(record.get(key)):
                raise ValueError(f"overlay {game} requires a valid {key}")
        _check_metadata(record.get("metadata"))
        records[game] = record
    return MetadataOverlay(path, hashlib.sha256(payload).hexdigest(), records, payload)
