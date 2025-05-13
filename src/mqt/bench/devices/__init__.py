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

from qiskit.circuit.controlflow import ControlFlowOp
from qiskit.circuit.library.standard_gates import __dict__ as gate_dict
from qiskit.transpiler import Target

from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

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
    return [device.description for device in get_available_devices()]


@cache
def _device_map() -> dict[str, Target]:
    """One-time build of name → Device map.

    Cached forever by functools.cache.
    """
    return {d.description: d for d in get_available_devices()}


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
        target = Target(description=f"{device.description}", num_qubits=num_qubits)

        for op_name in device.operation_names:  # ✅ Now using string names
            if op_name in {"reset", "barrier", "measure", "delay"}:
                continue

            inst_obj = device[op_name].default_inst

            # Skip control-flow ops
            if isinstance(inst_obj, ControlFlowOp):
                continue

            # Get class safely — handle singleton gates
            inst_class = inst_obj if isinstance(inst_obj, type) else type(inst_obj)

            try:
                target.add_instruction(inst_class)
            except TypeError:
                continue

        gatesets[target.description] = target
        print(gatesets)

    # Add custom Clifford+T gateset
    clifford = Target(num_qubits=num_qubits, description="clifford+t")

    for name in [
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
    ]:
        gate_class = gate_dict[name.upper()]
        clifford.add_instruction(gate_class)  # ✅ pass class, not instance

    gatesets["clifford+t"] = clifford

    return gatesets


def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    """Retrieve an unrestricted gateset Target by name."""
    gatesets = get_available_native_gatesets(num_qubits)
    try:
        return gatesets[name]
    except KeyError:
        msg = f"Gateset '{name}' not found."
        raise ValueError(msg) from None


# === Exports ===

__all__ = [
    "get_available_device_names",
    "get_available_devices",
    "get_available_native_gatesets",
    "get_device_by_name",
    "get_native_gateset_by_name",
]
