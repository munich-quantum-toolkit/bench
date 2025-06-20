# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for IBM."""

from __future__ import annotations

from ._registry import register_gateset


@register_gateset("ibm_falcon")
def get_ibm_falcon_gateset() -> list[str]:
    """Returns the basis gates of the IBM Falcon gateset."""
    return ["id", "x", "sx", "rz", "cx"]


@register_gateset("ibm_eagle")
def get_ibm_eagle_gateset() -> list[str]:
    """Returns the basis gates of the IBM Eagle gateset."""
    return ["id", "x", "sx", "rz", "ecr"]


@register_gateset("ibm_heron")
def get_ibm_heron_gateset() -> list[str]:
    """Returns the basis gates of the IBM Heron gateset."""
    return ["id", "x", "sx", "rz", "cz"]
