from __future__ import annotations


def get_clifford_t_gateset() -> list[str]:
    """Returns the native gateset for Clifford+T."""
    return [
        "id",
        "x",
        "y",
        "z",
        "h",
        "s",
        "sdg",
        "t",
        "tdg",
        "sx",
        "sxdg",
        "cx",
        "cy",
        "cz",
        "swap",
        "iswap",
        "dcx",
        "ecr",
    ]


def get_clifford_t_rotations_gateset() -> list[str]:
    """Returns the native gateset for the Clifford+T plus rotation gates."""
    return [
        *get_clifford_t_gateset(),
        "rx",
        "ry",
        "rz",
    ]
