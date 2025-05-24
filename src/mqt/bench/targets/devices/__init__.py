# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the devices module."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from ._registry import all_devices, device_names, get_device
from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

if TYPE_CHECKING:
    from qiskit.transpiler import Target


__all__ = [
    "get_available_device_names",
    "get_available_devices",
    "get_device_by_name",
    "get_ibm_target",
    "get_ionq_target",
    "get_iqm_target",
    "get_quantinuum_target",
    "get_rigetti_target",
]


@cache
def get_available_devices() -> list[Target]:
    """Return a list of available devices."""
    return all_devices()


@cache
def get_available_device_names() -> list[str]:
    """Return a list of available device names."""
    return device_names()


@cache
def get_device_by_name(device_name: str) -> Target:
    """Return the Target object for a given device name."""
    try:
        return get_device(device_name)
    except KeyError:
        msg = f"Unknown device '{device_name}'. Available devices: {get_available_device_names()}"
        raise ValueError(msg) from None
