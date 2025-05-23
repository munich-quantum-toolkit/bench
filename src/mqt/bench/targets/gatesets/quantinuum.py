from __future__ import annotations


def get_quantinuum_gateset() -> list[str]:
    """Returns the basis gates of the Quantinuum gateset."""
    return ["rx", "ry", "rz", "rzz"]
