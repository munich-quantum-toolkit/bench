# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the targets module."""

from __future__ import annotations

from .devices import get_available_device_names, get_device
from .gatesets import (
    get_available_gateset_names,
    get_gateset,
    get_target_for_gateset,
)

__all__ = [
    "get_available_device_names",
    "get_available_gateset_names",
    "get_device",
    "get_gateset",
    "get_target_for_gateset",
]
