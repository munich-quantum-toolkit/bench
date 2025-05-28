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

from . import _registry as device_registry
from . import ibm, ionq, iqm, quantinuum, rigetti

if TYPE_CHECKING:
    from qiskit.transpiler import Target


__all__ = [
    "device_registry",
    "get_available_device_names",
    "get_available_devices",
    "get_device",
    "ibm",
    "ionq",
    "iqm",
    "quantinuum",
    "rigetti",
]


@cache
def get_available_devices() -> dict[str, Target]:
    """Return a dict of available devices."""
    return device_registry.all_devices()


@cache
def get_available_device_names() -> list[str]:
    """Return a list of available device names."""
    return device_registry.device_names()


@cache
def get_device(device_name: str) -> Target:
    """Return the Target object for a given device name."""
    try:
        return device_registry.get_device_by_name(device_name)
    except KeyError:
        msg = f"Unknown device '{device_name}'. Available devices: {get_available_device_names()}"
        raise ValueError(msg) from None
