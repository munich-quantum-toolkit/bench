# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for IQM."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("iqm")
def get_iqm_gateset() -> list[str]:
    """Returns the basis gates of the IQM gateset."""
    return ["r", "cz"]
