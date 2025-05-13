# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""MQT Bench.

This file is part of the MQT Bench Benchmark library released under the MIT license.
See README.md or go to https://github.com/cda-tum/mqt-bench for more information.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .device import Gateset
from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

if TYPE_CHECKING:
    from qiskit.transpiler import Target


@cache
def get_available_devices() -> list[Target]:
    """Get a list of all available devices."""
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
    """Get a list of all available device names."""
    return [device.name for device in get_available_devices()]


@cache
def _device_map() -> dict[str, Target]:
    """One-time build of name → Device map.

    Cached forever by functools.cache.
    """
    return {d.name: d for d in get_available_devices()}


def get_device_by_name(device_name: str) -> Target:
    """Get a device by its name.

    Arguments:
        device_name: the name of the device
    """
    try:
        return _device_map()[device_name]
    except KeyError:
        msg = f"Device {device_name} not found in available devices."
        raise ValueError(msg) from None


__all__ = [
    "Gateset",
    "get_available_device_names",
    "get_available_devices",
    "get_device_by_name",
]


@cache
def get_available_native_gatesets() -> list[Gateset]:
    """Get a list of all available native gatesets."""
    available_gatesets = []
    for device in get_available_devices():
        if device.gateset not in available_gatesets:
            available_gatesets.append(device.gateset)
    available_gatesets.append(
        Gateset(
            "clifford+t",
            [
                "i",
                "x",
                "y",
                "z",
                "h",
                "s",
                "sdg",
                "t",
                "tdg",
                "sx",
                "sxdg",
                "cx",
                "cy",
                "cz",
                "swap",
                "iswap",
                "dcx",
                "ecr",
                "measure",
                "barrier",
            ],
        )
    )
    return available_gatesets


@cache
def _native_gateset_map() -> dict[str, Gateset]:
    """One-time build of name → Gateset map.

    Cached forever by functools.cache.
    """
    return {g.name: g for g in get_available_native_gatesets()}


def get_native_gateset_by_name(gateset_name: str) -> Gateset:
    """Get a native gateset by its name.

    Arguments:
        gateset_name: the name of the gateset
    """
    try:
        return _native_gateset_map()[gateset_name]
    except KeyError:
        msg = f"Gateset {gateset_name} not found in available gatesets."
        raise ValueError(msg) from None
