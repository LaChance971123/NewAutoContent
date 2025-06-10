from __future__ import annotations

"""Simple story generator placeholder."""

from typing import Optional


def generate_story(genre: Optional[str] = None, tone: Optional[str] = None, prompt: Optional[str] = None) -> str:
    """Return a basic story text influenced by *genre*, *tone*, and *prompt*."""
    base = prompt or "Once upon a time there was a short story."
    if genre:
        base = f"A {genre} story: {base}"
    if tone:
        base = f"({tone} tone) " + base
    return base
