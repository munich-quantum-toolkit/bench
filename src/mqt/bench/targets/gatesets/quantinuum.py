# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for Quantinuum."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("quantinuum")
def get_quantinuum_gateset() -> list[str]:
    """Returns the basis gates of the Quantinuum gateset."""
    return ["rx", "ry", "rz", "rzz"]
