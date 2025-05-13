# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the Rigetti calibration data."""
# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qiskit.circuit import Parameter
from qiskit.circuit.library import CPhaseGate, CZGate, Measure, RXGate, RZGate, XXPlusYYGate
from qiskit.transpiler import InstructionProperties, Target

from .calibration import get_device_calibration_path

if TYPE_CHECKING:
    from pathlib import Path


def create_rigetti_target(calibration_path: Path) -> Target:
    """Create a target device from the Rigetti calibration data.

    This function creates a Qiskit Target object representing Rigetti's quantum device
    capabilities, including supported gate operations and their properties based on
    device calibration data.

    Args:
        calibration_path: Path to the JSON file containing Rigetti device calibration data

    Returns:
        Target: A Qiskit Target object containing:
            - Device topology and connectivity
            - Supported single-qubit gates (RZ, RX)
            - Supported two-qubit gates (CZ, CPhase, XXPlusYY)
            - Gate error rates and fidelities
            - Measurement capabilities
    """
    with calibration_path.open() as f:
        data = json.load(f)

    target = Target(num_qubits=data["num_qubits"], description=data["name"])

    # Parameters
    theta = Parameter("theta")
    alpha = Parameter("alpha")
    lam = Parameter("lambda")
    phi = Parameter("phi")

    oneq_props = data["properties"]["1Q"]

    # === Aggregate properties for RZ and Measure ===
    rz_props = {}
    measure_props = {}

    # === Add RXGate only once per fixed angle with all qubits ===

    rx_props = {}
    for q_str, props in data["properties"]["1Q"].items():
        q = from_rigetti_index(int(q_str))
        fidelity = props["f1QRB"]
        rx_props[q,] = InstructionProperties(error=1 - fidelity)
    target.add_instruction(RXGate(alpha), rx_props)

    for q_str, props in oneq_props.items():
        q = from_rigetti_index(int(q_str))
        rz_props[q,] = InstructionProperties(error=0.0)
        measure_props[q,] = InstructionProperties(error=1 - props["fRO"])

    target.add_instruction(RZGate(lam), rz_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    # === Aggregate all two-qubit properties first ===
    cz_props = {}
    cp_props = {}
    xy_props = {}
    added_pairs = set()

    for a, b in data["connectivity"]:
        q1 = from_rigetti_index(a)
        q2 = from_rigetti_index(b)
        if (q1, q2) in added_pairs or (q2, q1) in added_pairs:
            continue
        added_pairs.add((q1, q2))

        edge_key = f"{a}-{b}"
        fidelity_info = data["properties"]["2Q"].get(edge_key, {})

        if "fCZ" in fidelity_info:
            fcz = fidelity_info["fCZ"]
            cz_props[q1, q2] = InstructionProperties(error=1 - fcz)
            cz_props[q2, q1] = InstructionProperties(error=1 - fcz)
        if "fCPHASE" in fidelity_info:
            fcp = fidelity_info["fCPHASE"]
            cp_props[q1, q2] = InstructionProperties(error=1 - fcp)
            cp_props[q2, q1] = InstructionProperties(error=1 - fcp)
        if "fXY" in fidelity_info:
            fxy = fidelity_info["fXY"]
            xy_props[q1, q2] = InstructionProperties(error=1 - fxy)
            xy_props[q2, q1] = InstructionProperties(error=1 - fxy)

    # === Fill missing entries with averages (optional) ===
    all_pairs = {
        (from_rigetti_index(a), from_rigetti_index(b))
        for a, b in data["connectivity"]
        if (from_rigetti_index(a), from_rigetti_index(b)) not in added_pairs
        and (from_rigetti_index(b), from_rigetti_index(a)) not in added_pairs
    }

    cz_avg = sum(1 - v.error for v in cz_props.values()) / len(cz_props) if cz_props else None
    cp_avg = sum(1 - v.error for v in cp_props.values()) / len(cp_props) if cp_props else None
    xy_avg = sum(1 - v.error for v in xy_props.values()) / len(xy_props) if xy_props else None

    for q1, q2 in all_pairs:
        if (q1, q2) not in cz_props and cz_avg:
            cz_props[q1, q2] = InstructionProperties(error=1 - cz_avg)
        if (q1, q2) not in cp_props and cp_avg:
            cp_props[q1, q2] = InstructionProperties(error=1 - cp_avg)
        if (q1, q2) not in xy_props and xy_avg:
            xy_props[q1, q2] = InstructionProperties(error=1 - xy_avg)

    # === Finally, add each instruction type ONCE ===
    if cz_props:
        target.add_instruction(CZGate(), cz_props)
    if cp_props:
        target.add_instruction(CPhaseGate(phi), cp_props)
    if xy_props:
        target.add_instruction(XXPlusYYGate(theta), xy_props)

    return target


def get_rigetti_target(device_name: str) -> Target:
    """Get a target device from the Rigetti calibration data."""
    return create_rigetti_target(get_device_calibration_path(device_name))


def from_rigetti_index(rigetti_index: int) -> int:
    """Convert the Rigetti qubit index to a consecutive index.

    The Rigetti architectures consist of 8-qubit rings arranged in a two-dimensional grid.
    Each qubit is identified by a three digit number, where:
      * the first digit is the row index,
      * the second digit is the column index, and
      * the third digit is the ring index.

    Arguments:
        rigetti_index: the Rigetti qubit index

    Returns: the consecutive index
    """
    ring_size = 8
    columns = 5
    row = rigetti_index // 100
    column = (rigetti_index % 100) // 10
    ring = rigetti_index % 10
    qubit_indx = row * (ring_size * columns) + column * ring_size + ring
    # Account for missing qubit in Aspen-M3
    # rigetti_index: 136 = qubit_indx: 70
    if qubit_indx >= 70:
        qubit_indx = qubit_indx - 1
    return qubit_indx


def to_rigetti_index(index: int) -> int:
    """Convert the consecutive index to the Rigetti qubit index.

    Arguments:
        index: the consecutive index.

    Returns: the Rigetti qubit index
    """
    # Account for missing qubit in Aspen-M3
    # rigetti_index: 136 = qubit_indx: 70
    if index >= 70:
        index = index + 1
    ring_size = 8
    columns = 5
    row = index // (ring_size * columns)
    column = (index % (ring_size * columns)) // ring_size
    ring = (index % (ring_size * columns)) % ring_size
    return row * 100 + column * 10 + ring
