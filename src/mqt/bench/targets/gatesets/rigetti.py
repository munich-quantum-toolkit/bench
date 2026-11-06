# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Fixed-angle RX gates and arbitrary RZ rotations for Rigetti targets."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("rigetti")
def get_rigetti_gateset() -> list[str]:
    """Return the RX/RZ/CZ basis used by Cepheus."""
    return ["rxpi", "rxpidg", "rxpi2", "rxpi2dg", "rz", "cz", "measure"]
