from __future__ import annotations

import hashlib
import pathlib


def validate_key(key: str) -> str:
    cleaned = key.strip()
    if not cleaned:
        raise ValueError
    return cleaned


def key_to_relpath(key: str) -> pathlib.Path:
    digest = hashlib.blake2b(
        validate_key(key).encode("utf-8"), digest_size=16
    ).hexdigest()
    return pathlib.Path(digest[:2]) / digest[2:4] / digest
