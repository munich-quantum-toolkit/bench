from __future__ import annotations


def get_ibm_falcon_gateset() -> list[str]:
    """Returns the basis gates of the IBM Falcon gateset."""
    return ["id", "x", "sx", "rz", "cx"]


def get_ibm_eagle_gateset() -> list[str]:
    """Returns the basis gates of the IBM Eagle gateset."""
    return ["id", "x", "sx", "rz", "ecr"]


def get_ibm_heron_gateset() -> list[str]:
    """Returns the basis gates of the IBM Heron gateset."""
    return ["id", "x", "sx", "rz", "cz"]
