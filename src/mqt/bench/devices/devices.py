# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the devices module."""

from __future__ import annotations


from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target
from functools import cache

@cache
def get_available_devices() -> list[Target]:
    """Return a list of available devices."""
    return [
        get_ibm_target("ibm_montreal"),
        get_ibm_target("ibm_torino"),
        get_ibm_target("ibm_washington"),
        get_ionq_target("ionq_harmony"),
        get_ionq_target("ionq_aria1"),
        get_iqm_target("iqm_adonis"),
        get_iqm_target("iqm_apollo"),
        get_quantinuum_target("quantinuum_h2"),
        get_rigetti_target("rigetti_aspen_m3"),
    ]

@cache
def get_available_device_names() -> list[str]:
    """Return a list of available device names."""
    return [device.description for device in get_available_devices()]


@cache
def _device_map() -> dict[str, Target]:
    """Return a mapping of device names to Target objects."""
    return {d.description: d for d in get_available_devices()}


def get_device_by_name(device_name: str) -> Target:
    """Return the Target object for a given device name."""
    try:
        return _device_map()[device_name]
    except KeyError:
        msg = f"Device {device_name} not found."
        raise ValueError(msg) from None