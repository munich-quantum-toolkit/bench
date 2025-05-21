# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the targets module."""

from __future__ import annotations

from .devices import get_available_devices, get_device_by_name
from .gatesets import (
    get_available_native_gatesets,
    get_target_for_gateset,
)

__all__ = [
    "get_available_devices",
    "get_available_native_gatesets",
    "get_device_by_name",
    "get_target_for_gateset",
]
