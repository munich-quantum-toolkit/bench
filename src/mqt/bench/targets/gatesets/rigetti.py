from __future__ import annotations


def get_rigetti_gateset() -> list[str]:
    """Returns the basis gates of the Rigetti gateset."""
    return ["rx", "rz", "cz", "cp", "xx_plus_yy"]
