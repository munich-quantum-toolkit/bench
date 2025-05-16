# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets."""

from __future__ import annotations

from functools import cache

from qiskit.circuit import Barrier, Instruction, Measure
from qiskit.circuit.library import (
    CXGate,
    CYGate,
    CZGate,
    DCXGate,
    ECRGate,
    HGate,
    IGate,
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

from mqt.bench.devices import get_available_devices

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


def create_clifford_t_target(num_qubits: int) -> Target:
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
        target.add_instruction(gate_class())

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
    gatesets["clifford+t"] = create_clifford_t_target(num_qubits=num_qubits)
    return gatesets


def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    """Return the Target object for a given native gateset name."""
    gatesets = get_available_native_gatesets(num_qubits)
    try:
        return gatesets[name]
    except KeyError:
        msg = f"Gateset '{name}' not found in available gatesets."
        raise ValueError(msg) from None
