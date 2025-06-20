# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create target devices for IQM with hardcoded mean calibration data."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, RGate
from qiskit.transpiler import InstructionProperties, Target

from ._registry import register_device


@register_device("iqm_crystal_5")
def get_iqm_crystal_5() -> Target:
    """Get the target for a 5-qubit IQM Crystal architecture."""
    return _build_iqm_target(
        name="iqm_crystal_5",
        num_qubits=5,
        connectivity=[[0, 2], [2, 0], [1, 2], [2, 1], [3, 2], [2, 3], [4, 2], [2, 4]],
        oneq_error=0.00132,
        twoq_error=0.0311,
        readout_error=0.0278,
        oneq_duration=4e-8,
        twoq_duration=8e-8,
        readout_duration=1.5e-5,
    )


@register_device("iqm_crystal_20")
def get_iqm_crystal_20() -> Target:
    """Get the target for a 20-qubit IQM Crystal architecture."""
    return _build_iqm_target(
        name="iqm_crystal_20",
        num_qubits=20,
        connectivity=[
            [0, 1],
            [0, 3],
            [1, 4],
            [2, 3],
            [7, 2],
            [3, 4],
            [8, 3],
            [4, 5],
            [9, 4],
            [5, 6],
            [10, 5],
            [11, 6],
            [7, 8],
            [7, 12],
            [8, 9],
            [8, 13],
            [9, 10],
            [9, 14],
            [10, 11],
            [15, 10],
            [16, 11],
            [12, 13],
            [13, 14],
            [17, 13],
            [15, 14],
            [18, 14],
            [15, 16],
            [15, 19],
            [17, 18],
            [18, 19],
        ],
        oneq_error=0.001259,
        twoq_error=0.01474,
        readout_error=0.05075,
        oneq_duration=4.2e-8,
        twoq_duration=1.3e-7,
        readout_duration=1.5e-5,
    )


@register_device("iqm_crystal_54")
def get_iqm_crystal_54() -> Target:
    """Get the target for a 54-qubit IQM Crystal architecture."""
    return _build_iqm_target(
        name="iqm_crystal_54",
        num_qubits=54,
        connectivity=[
            [0, 1],
            [0, 4],
            [1, 5],
            [2, 3],
            [2, 8],
            [3, 4],
            [3, 9],
            [4, 5],
            [4, 10],
            [5, 6],
            [5, 11],
            [6, 12],
            [7, 8],
            [7, 15],
            [8, 9],
            [8, 16],
            [9, 10],
            [9, 17],
            [10, 11],
            [10, 18],
            [11, 12],
            [11, 19],
            [12, 13],
            [12, 20],
            [13, 21],
            [14, 15],
            [14, 22],
            [15, 16],
            [15, 23],
            [16, 17],
            [16, 24],
            [17, 18],
            [17, 25],
            [18, 19],
            [18, 26],
            [19, 20],
            [19, 27],
            [20, 21],
            [20, 28],
            [21, 29],
            [22, 23],
            [23, 24],
            [23, 31],
            [24, 25],
            [24, 32],
            [25, 26],
            [25, 33],
            [26, 27],
            [26, 34],
            [27, 28],
            [27, 35],
            [28, 29],
            [28, 36],
            [29, 30],
            [29, 37],
            [30, 38],
            [31, 32],
            [31, 39],
            [32, 33],
            [32, 40],
            [33, 34],
            [33, 41],
            [34, 35],
            [34, 42],
            [35, 36],
            [35, 43],
            [36, 37],
            [36, 44],
            [37, 38],
            [37, 45],
            [39, 40],
            [40, 41],
            [40, 46],
            [41, 42],
            [41, 47],
            [42, 43],
            [42, 48],
            [43, 44],
            [43, 49],
            [44, 45],
            [44, 50],
            [46, 47],
            [47, 48],
            [47, 51],
            [48, 49],
            [48, 52],
            [49, 50],
            [49, 53],
            [51, 52],
            [52, 53],
        ],
        oneq_error=0.001259,
        twoq_error=0.01474,
        readout_error=0.05075,
        oneq_duration=4.2e-8,
        twoq_duration=1.3e-7,
        readout_duration=1.5e-5,
    )


def _build_iqm_target(
    *,
    name: str,
    num_qubits: int,
    connectivity: list[list[int]],
    oneq_error: float,
    twoq_error: float,
    readout_error: float,
    oneq_duration: float,
    twoq_duration: float,
    readout_duration: float,
) -> Target:
    """Construct a hardcoded IQM target using mean values."""
    target = Target(num_qubits=num_qubits, description=name)

    theta = Parameter("theta")
    phi = Parameter("phi")

    # === Add single-qubit gates ===
    r_props = {(q,): InstructionProperties(duration=oneq_duration, error=oneq_error) for q in range(num_qubits)}
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=readout_error) for q in range(num_qubits)
    }

    target.add_instruction(RGate(theta, phi), r_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    cz_props = {(q1, q2): InstructionProperties(duration=twoq_duration, error=twoq_error) for q1, q2 in connectivity}
    target.add_instruction(CZGate(), cz_props)

    return target
