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

from qiskit.transpiler import Target

from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

if TYPE_CHECKING:
    from qiskit.transpiler import Target


# === Device Access ===

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


# === Native Gatesets ===

@cache
def get_available_native_gatesets(num_qubits: int = 20) -> dict[str, Target]:
    """Return mapping: gateset_name → unrestricted Target for up to `num_qubits`."""
    gatesets = {}

    for device in get_available_devices():
        target = Target(name=f"{device.name}_gateset", num_qubits=num_qubits)
        for inst_name in device.operations:
            inst = device[inst_name].default_inst
            target.add_instruction(inst)
        gatesets[target.name] = target

    # Add custom Clifford+T gateset
    from qiskit.circuit.library.standard_gates import __dict__ as gate_dict
    clifford = Target(name="clifford+t", num_qubits=num_qubits)
    for name in [
        "i", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "sx", "sxdg",
        "cx", "cy", "cz", "swap", "iswap", "dcx", "ecr", "measure", "barrier"
    ]:
        try:
            gate_class = gate_dict[name.upper()]
            inst = gate_class()
            clifford.add_instruction(inst)
        except Exception:
            continue
    gatesets["clifford+t"] = clifford

    return gatesets


def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    """Retrieve an unrestricted gateset Target by name."""
    gatesets = get_available_native_gatesets(num_qubits)
    try:
        return gatesets[name]
    except KeyError:
        raise ValueError(f"Gateset '{name}' not found.") from None


# === Exports ===

__all__ = [
    "get_available_devices",
    "get_available_device_names",
    "get_device_by_name",
    "get_available_native_gatesets",
    "get_native_gateset_by_name",
]