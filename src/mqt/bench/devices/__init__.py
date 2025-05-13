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

from qiskit.circuit import Instruction
from qiskit.circuit.library import (
    Barrier,
    CXGate,
    CYGate,
    CZGate,
    DCXGate,
    ECRGate,
    HGate,
    IGate,
    Measure,
    SdgGate,
    SGate,
    SwapGate,
    SXdgGate,
    SXGate,
    TdgGate,
    TGate,
    XGate,
    YGate,
    ZGate,
    iSwapGate,
)
from qiskit.transpiler import Target

from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

DEVICE_TO_GATESET = {
    "ibm_montreal": "ibm_falcon",
    "ibm_washington": "ibm_falcon",
    "ibm_torino": "ibm_heron_r1",
    "ionq_harmony": "ionq",
    "ionq_aria1": "ionq",
    "iqm_adonis": "iqm",
    "iqm_apollo": "iqm",
    "quantinuum_h2": "quantinuum",
    "rigetti_aspen_m3": "rigetti",
}


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


def create_clifford_target(num_qubits: int) -> Target:
    """Create a dense Target for the Clifford+T gateset with full qubit connectivity."""
    gate_classes = {
        "i": IGate,
        "x": XGate,
        "y": YGate,
        "z": ZGate,
        "h": HGate,
        "s": SGate,
        "sdg": SdgGate,
        "t": TGate,
        "tdg": TdgGate,
        "sx": SXGate,
        "sxdg": SXdgGate,
        "cx": CXGate,
        "cy": CYGate,
        "cz": CZGate,
        "swap": SwapGate,
        "iswap": iSwapGate,
        "dcx": DCXGate,
        "ecr": ECRGate,
        "measure": Measure,
        "barrier": lambda: Barrier(num_qubits),
    }

    target = Target(num_qubits=num_qubits, description="clifford+t")

    for gate_class in gate_classes.values():
        try:
            gate = gate_class()

            if gate.name == "barrier":
                qargs = {tuple(range(num_qubits)): None}
            elif gate.num_qubits == 1:
                qargs = {(q,): None for q in range(num_qubits)}
            elif gate.num_qubits == 2:
                qargs = {(q0, q1): None for q0 in range(num_qubits) for q1 in range(num_qubits) if q0 != q1}
            else:
                continue  # skip 3+ qubit gates (not needed here)

            target.add_instruction(gate, qargs)
        except Exception:
            continue

    return target


@cache
def get_available_native_gatesets(num_qubits: int = 20) -> dict[str, Target]:
    """Return mapping: gateset_name → Target (deduplicated)."""
    gatesets: dict[str, Target] = {}

    for device in get_available_devices():
        device_name = device.description
        gateset_name = DEVICE_TO_GATESET[device_name]

        if gateset_name in gatesets:
            continue  # already built

        target = Target(description=gateset_name, num_qubits=num_qubits)

        for op_name in device.operation_names:
            try:
                # Access instruction mapping (could be a dict or custom object)
                op_entry = device[op_name]

                # Skip if empty or invalid
                if not isinstance(op_entry, dict) or not op_entry:
                    continue

                # Try to resolve the instruction object
                try:
                    inst = device.operation_from_name(op_name)
                except Exception:
                    continue

                # Validate it's a real Instruction and not a class
                if not isinstance(inst, Instruction):
                    try:
                        inst = inst()  # instantiate if it's a class
                    except Exception:
                        continue

                # Prepare qubit mappings
                qarg_map = dict.fromkeys(op_entry.keys())
                if qarg_map:
                    target.add_instruction(inst, qarg_map)

            except Exception as e:
                print(f"Skipping {op_name}: {e}")
                continue

        gatesets[gateset_name] = target

    # Add Clifford+T manually
    gatesets["clifford+t"] = create_clifford_target(num_qubits=num_qubits)
    return gatesets


def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    """Return the Target object for a given native gateset name."""
    gatesets = get_available_native_gatesets(num_qubits)
    try:
        return gatesets[name]
    except KeyError:
        msg = f"Gateset '{name}' not found in available gatesets."
        raise ValueError(msg) from None


__all__ = [
    "get_available_device_names",
    "get_available_devices",
    "get_available_native_gatesets",
    "get_device_by_name",
    "get_native_gateset_by_name",
]
