"""Collision-safe paths for generated artifacts and evidence."""

from __future__ import annotations

from pathlib import Path


def available_path(path: Path) -> Path:
    """Return the requested path or a numbered sibling without overwriting content."""
    if not path.exists():
        return path

    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1
