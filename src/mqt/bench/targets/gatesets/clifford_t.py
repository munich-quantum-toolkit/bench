# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the native gateset for Clifford+T."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("clifford+t")
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


@register_gateset("clifford+t+rotations")
def get_clifford_t_rotations_gateset() -> list[str]:
    """Returns the native gateset for the Clifford+T plus rotation gates."""
    return [
        *get_clifford_t_gateset(),
        "rx",
        "ry",
        "rz",
    ]
