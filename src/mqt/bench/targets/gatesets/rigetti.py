# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for Rigetti."""

from __future__ import annotations


def get_rigetti_gateset() -> list[str]:
    """Returns the basis gates of the Rigetti gateset."""
    return ["rx", "rz", "cz", "cp", "xx_plus_yy"]
