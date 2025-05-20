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


def get_iqm_target(device_name: str) -> Target:
    """Get a hardcoded IQM target device by name."""
    if device_name == "iqm_adonis":
        return get_iqm_adonis_target()
    if device_name == "iqm_apollo":
        return get_iqm_apollo_target()
    msg = f"Unknown IQM device: {device_name}"
    raise ValueError(msg)


def get_iqm_adonis_target() -> Target:
    """Get the target device for IQM Adonis."""
    return _build_iqm_target(
        name="iqm_adonis",
        num_qubits=5,
        connectivity=[[0, 2], [2, 0], [1, 2], [2, 1], [3, 2], [2, 3], [4, 2], [2, 4]],
        oneq_error=0.00132,
        twoq_error=0.0311,
        readout_error=0.0278,
        oneq_duration=4e-8,
        twoq_duration=8e-8,
        readout_duration=1.5e-5,
    )


def get_iqm_apollo_target() -> Target:
    """Get the target device for IQM Apollo."""
    return _build_iqm_target(
        name="iqm_apollo",
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

    # === Single-qubit R gate ===
    r_props = {(q,): InstructionProperties(duration=oneq_duration, error=oneq_error) for q in range(num_qubits)}
    target.add_instruction(RGate(theta, phi), r_props)

    # === Per-qubit measurement ===
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=readout_error) for q in range(num_qubits)
    }
    target.add_instruction(Measure(), measure_props)

    # === Two-qubit CZ gate ===
    cz_props = {}
    for q1, q2 in connectivity:
        props = InstructionProperties(duration=twoq_duration, error=twoq_error)
        cz_props[q1, q2] = props
        cz_props[q2, q1] = props  # assume symmetric

    target.add_instruction(CZGate(), cz_props)

    return target
