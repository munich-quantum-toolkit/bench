# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the Rigetti calibration data."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import CPhaseGate, CZGate, Measure, RXGate, RZGate, XXPlusYYGate
from qiskit.transpiler import InstructionProperties, Target


def get_rigetti_target(device_name: str) -> Target:
    """Get a hardcoded Rigetti target device by name."""
    if device_name == "rigetti_aspen_m3":
        return get_rigetti_aspen_m3_target()
    msg = f"Unknown Rigetti device: '{device_name}'."
    raise ValueError(msg)


def get_rigetti_aspen_m3_target() -> Target:
    """Get the target device for Rigetti Aspen M3."""
    num_qubits = 79
    connectivity = [
        [0, 1],
        [0, 7],
        [0, 43],
        [1, 0],
        [1, 2],
        [1, 14],
        [2, 1],
        [2, 3],
        [2, 13],
        [3, 2],
        [3, 4],
        [4, 3],
        [4, 5],
        [5, 4],
        [5, 6],
        [6, 5],
        [6, 7],
        [7, 0],
        [7, 6],
        [7, 44],
        [8, 9],
        [8, 15],
        [8, 51],
        [9, 8],
        [9, 10],
        [9, 22],
        [10, 9],
        [10, 11],
        [10, 21],
        [11, 10],
        [11, 12],
        [12, 11],
        [12, 13],
        [13, 2],
        [13, 12],
        [13, 14],
        [14, 1],
        [14, 13],
        [14, 15],
        [15, 8],
        [15, 14],
        [15, 52],
        [16, 17],
        [16, 23],
        [16, 59],
        [17, 16],
        [17, 18],
        [17, 30],
        [18, 17],
        [18, 19],
        [18, 29],
        [19, 18],
        [19, 20],
        [20, 19],
        [20, 21],
        [21, 10],
        [21, 20],
        [21, 22],
        [22, 9],
        [22, 21],
        [22, 23],
        [23, 16],
        [23, 22],
        [23, 60],
        [24, 25],
        [24, 31],
        [24, 67],
        [25, 24],
        [25, 26],
        [25, 38],
        [26, 25],
        [26, 27],
        [26, 37],
        [27, 26],
        [27, 28],
        [28, 27],
        [28, 29],
        [29, 18],
        [29, 28],
        [29, 30],
        [30, 17],
        [30, 29],
        [30, 31],
        [31, 24],
        [31, 30],
        [31, 68],
        [32, 33],
        [32, 39],
        [32, 74],
        [33, 32],
        [33, 34],
        [34, 33],
        [34, 35],
        [35, 34],
        [35, 36],
        [36, 35],
        [37, 26],
        [37, 38],
        [38, 25],
        [38, 37],
        [38, 39],
        [39, 32],
        [39, 38],
        [39, 75],
        [40, 41],
        [40, 47],
        [41, 40],
        [41, 42],
        [41, 54],
        [42, 41],
        [42, 43],
        [42, 53],
        [43, 0],
        [43, 42],
        [43, 44],
        [44, 7],
        [44, 43],
        [44, 45],
        [45, 44],
        [45, 46],
        [46, 45],
        [46, 47],
        [47, 40],
        [47, 46],
        [48, 49],
        [48, 55],
        [49, 48],
        [49, 50],
        [49, 62],
        [50, 49],
        [50, 51],
        [50, 61],
        [51, 8],
        [51, 50],
        [51, 52],
        [52, 15],
        [52, 51],
        [52, 53],
        [53, 42],
        [53, 52],
        [53, 54],
        [54, 41],
        [54, 53],
        [54, 55],
        [55, 48],
        [55, 54],
        [56, 57],
        [56, 63],
        [57, 56],
        [57, 58],
        [57, 70],
        [58, 57],
        [58, 59],
        [58, 69],
        [59, 16],
        [59, 58],
        [59, 60],
        [60, 23],
        [60, 59],
        [60, 61],
        [61, 50],
        [61, 60],
        [61, 62],
        [62, 49],
        [62, 61],
        [62, 63],
        [63, 56],
        [63, 62],
        [64, 65],
        [64, 70],
        [65, 64],
        [65, 66],
        [65, 77],
        [66, 65],
        [66, 67],
        [66, 76],
        [67, 24],
        [67, 66],
        [67, 68],
        [68, 31],
        [68, 67],
        [68, 69],
        [69, 58],
        [69, 68],
        [69, 70],
        [70, 64],
        [70, 69],
        [70, 57],
        [71, 72],
        [71, 78],
        [72, 71],
        [72, 73],
        [73, 72],
        [73, 74],
        [74, 32],
        [74, 73],
        [74, 75],
        [75, 39],
        [75, 74],
        [75, 76],
        [76, 66],
        [76, 75],
        [76, 77],
        [77, 65],
        [77, 76],
        [77, 78],
        [78, 71],
        [78, 77],
    ]
    return _build_rigetti_target(
        name="rigetti_aspen_m3",
        num_qubits=num_qubits,
        connectivity=connectivity,
        oneq_error=0.00375,
        twoq_error_cp=0.1186,
        twoq_error_cz=0.0974,
        twoq_error_xy=0.0893,
        spam_error=0.05468,
    )


def _build_rigetti_target(
    *,
    name: str,
    num_qubits: int,
    connectivity: list[list[int]],
    oneq_error: float,
    twoq_error_cp: float,
    twoq_error_cz: float,
    twoq_error_xy: float,
    spam_error: float,
) -> Target:
    """Construct a hardcoded Rigetti target using mean values."""
    target = Target(num_qubits=num_qubits, description=name)

    alpha = Parameter("alpha")
    beta = Parameter("beta")
    gamma = Parameter("gamma")
    theta = Parameter("theta")

    # === Add single-qubit gates ===
    single_qubit_gate_props = {(q,): InstructionProperties(error=oneq_error) for q in range(num_qubits)}
    measure_props = {(q,): InstructionProperties(error=spam_error) for q in range(num_qubits)}

    target.add_instruction(RXGate(alpha), single_qubit_gate_props)
    target.add_instruction(RZGate(beta), single_qubit_gate_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    cp_props = {(q1, q2): InstructionProperties(error=twoq_error_cp) for q1, q2 in connectivity}
    cz_props = {(q1, q2): InstructionProperties(error=twoq_error_cz) for q1, q2 in connectivity}
    xy_props = {(q1, q2): InstructionProperties(error=twoq_error_xy) for q1, q2 in connectivity}
    target.add_instruction(CPhaseGate(gamma), cp_props)
    target.add_instruction(CZGate(), cz_props)
    target.add_instruction(XXPlusYYGate(theta), xy_props)

    return target
