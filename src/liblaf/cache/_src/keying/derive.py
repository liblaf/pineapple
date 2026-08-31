from __future__ import annotations

import hashlib
import pathlib


def validate_key(key: str) -> str:
    """Normalize a non-empty caller-provided cache key.

    Args:
        key: Meaningful string identifier for one cache entry.

    Returns:
        `key` with surrounding whitespace removed.

    Raises:
        ValueError: If the resulting key is empty.

    Examples:
        >>> validate_key(" report/1 ")
        'report/1'
    """
    cleaned = key.strip()
    if not cleaned:
        raise ValueError
    return cleaned


def key_to_relpath(key: str) -> pathlib.Path:
    """Map a validated key to its deterministic relative entry path.

    The returned three-level path is a BLAKE2b digest, so user keys cannot
    escape the configured cache root.

    Args:
        key: Non-empty cache key.

    Returns:
        Relative path below a cache root.

    Examples:
        >>> key_to_relpath("answer").parts[:2]
        ('d7', '6c')
    """
    digest = hashlib.blake2b(
        validate_key(key).encode("utf-8"), digest_size=16
    ).hexdigest()
    return pathlib.Path(digest[:2]) / digest[2:4] / digest
