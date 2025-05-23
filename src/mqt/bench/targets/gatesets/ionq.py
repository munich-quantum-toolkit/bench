from __future__ import annotations


def get_ionq_gateset() -> list[str]:
    """Returns the basis gates of the IonQ gateset."""
    return ["rx", "ry", "rz", "rxx"]
