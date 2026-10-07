"""Public, read-only access to the arena API, with pacing, backoff and caching.

Only documented GET endpoints are used and no token is needed. Requests are
sequential and at most one per second; a 429 or 503 honours `Retry-After` and
backs off exponentially with jitter for at most five attempts. 400 and 404 are
errors to act on, never to retry in a loop. Replays are cached by game id with
atomic writes and a content checksum, and reused by every later stage.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://6s890.lids.mit.edu"
USER_AGENT = "iamavirus-learning/1.0 (MIT 6.7980 student bot; public read-only API)"
MIN_INTERVAL_SECONDS = 1.0
MAX_ATTEMPTS = 5


class ApiError(RuntimeError):
    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} for {url}: {body[:200]}")
        self.status = status
        self.url = url


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return sha256_bytes(data)


@dataclass
class FetchRecord:
    url: str
    fetched_at: str
    sha256: str
    status: int
    attempts: int


class ApiClient:
    def __init__(self, base_url: str = BASE_URL, min_interval: float = MIN_INTERVAL_SECONDS,
                 cache_dir: Path | None = None, timeout: float = 45.0):
        self.base_url = base_url.rstrip("/")
        self.min_interval = max(min_interval, MIN_INTERVAL_SECONDS)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self._last_request = 0.0
        self.requests_made = 0

    # -- transport ------------------------------------------------------------
    def _pace(self) -> None:
        wait = self._last_request + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)

    def get_bytes(self, path: str, params: dict | None = None) -> tuple[bytes, FetchRecord]:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        delay = 2.0
        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._pace()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                           "Accept": "application/json"})
            self._last_request = time.monotonic()
            self.requests_made += 1
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = response.read()
                    return data, FetchRecord(url, utc_now(), sha256_bytes(data), response.status, attempt)
            except urllib.error.HTTPError as error:
                body = error.read().decode("utf-8", "replace") if error.fp else ""
                if error.code in (400, 404):
                    raise ApiError(error.code, url, body) from None
                if error.code in (429, 503, 502, 504):
                    retry_after = error.headers.get("Retry-After") if error.headers else None
                    try:
                        wait = float(retry_after) if retry_after else delay
                    except ValueError:
                        wait = delay
                    wait = max(wait, delay) + random.uniform(0, 1.0)
                    last_error = ApiError(error.code, url, body)
                    if attempt < MAX_ATTEMPTS:
                        time.sleep(min(wait, 120.0))
                        delay = min(delay * 2, 60.0)
                        continue
                    raise last_error from None
                raise ApiError(error.code, url, body) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                last_error = error
                if attempt < MAX_ATTEMPTS:
                    time.sleep(delay + random.uniform(0, 1.0))
                    delay = min(delay * 2, 60.0)
                    continue
                raise
        raise RuntimeError(f"gave up on {url}: {last_error}")

    def get_json(self, path: str, params: dict | None = None) -> tuple[dict, FetchRecord]:
        data, record = self.get_bytes(path, params)
        return json.loads(data.decode("utf-8")), record

    # -- endpoints --------------------------------------------------------------
    def leaderboard(self) -> tuple[dict, FetchRecord]:
        return self.get_json("/api/leaderboard")

    def leaderboard_history(self) -> tuple[dict, FetchRecord]:
        return self.get_json("/api/leaderboard/history")

    def team_versions(self, team_id: str, cursor: int | None = None) -> tuple[dict, FetchRecord]:
        return self.get_json(f"/api/leaderboard/{urllib.parse.quote(team_id)}/versions",
                             {"cursor": cursor} if cursor is not None else None)

    def games_page(self, params: dict, cursor: str | None = None) -> tuple[dict, FetchRecord]:
        merged = dict(params)
        if cursor:
            merged["cursor"] = cursor
        return self.get_json("/api/games", merged)

    def iter_games(self, params: dict, limit: int | None = None):
        """Follows `nextCursor` sequentially, preserving filters and sort.

        Yields (summary, page_summary_from_first_page). The unfiltered `playing`
        array is ignored for training.
        """
        cursor = None
        first_summary = None
        yielded = 0
        base = {"sort": "played", "order": "desc", "limit": 100}
        base.update(params)
        while True:
            page, _ = self.games_page(base, cursor)
            if first_summary is None:
                first_summary = page.get("summary")
            for summary in page.get("games") or []:
                yield summary, first_summary
                yielded += 1
                if limit is not None and yielded >= limit:
                    return
            cursor = page.get("nextCursor")
            if not cursor:
                return

    def replay(self, game_id: str) -> tuple[dict, FetchRecord, bool]:
        """A completed game's replay, from cache when present. Returns (replay, record, cached)."""
        if self.cache_dir:
            path = self.cache_dir / "games" / game_id / "replay.json"
            meta = self.cache_dir / "games" / game_id / "fetch_metadata.json"
            if path.exists() and meta.exists():
                data = path.read_bytes()
                info = json.loads(meta.read_text())
                if info.get("replay", {}).get("sha256") == sha256_bytes(data):
                    rec = info["replay"]
                    return json.loads(data), FetchRecord(rec["url"], rec["fetched_at"], rec["sha256"], 200, 0), True
        data, record = self.get_bytes(f"/api/games/{game_id}")
        replay = json.loads(data.decode("utf-8"))
        return replay, record, False

    def diagnostics(self, game_id: str) -> tuple[dict, FetchRecord]:
        return self.get_json(f"/api/games/{game_id}/diagnostics")
