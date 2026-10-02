# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Native AQT gates in Qiskit's radian convention."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("aqt")
def get_aqt_gateset() -> list[str]:
    """Return AQT's phased rotations, Z rotations, and XX interactions."""
    return ["r", "rz", "rxx", "measure"]
