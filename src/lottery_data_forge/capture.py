from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .storage import Store


@dataclass(frozen=True)
class RawCapture:
    source_url: str
    retrieved_at: datetime
    source_hash: str
    content: bytes
    path: Path


def capture_url(
    url: str, raw_dir: Path, store: Store, timeout: float = 30.0
) -> RawCapture:
    retrieved_at = datetime.now(timezone.utc)
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    content = response.content
    source_hash = hashlib.sha256(content).hexdigest()
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{source_hash}.bin"
    path.write_bytes(content)
    store.save_raw(source_hash, url, retrieved_at.isoformat(), content)
    return RawCapture(url, retrieved_at, source_hash, content, path)


def verify_capture(path: Path, expected_hash: str) -> bool:
    return hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash
