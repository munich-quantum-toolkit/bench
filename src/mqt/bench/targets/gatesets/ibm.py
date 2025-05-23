# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for IBM."""

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
