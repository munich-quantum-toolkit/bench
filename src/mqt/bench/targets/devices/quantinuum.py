# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the Quantinuum calibration data."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RXGate, RYGate, RZGate, RZZGate
from qiskit.transpiler import InstructionProperties, Target


def get_quantinuum_target(device_name: str) -> Target:
    """Get a hardcoded Quantinuum target device by name."""
    if device_name == "quantinuum_h2":
        return get_quantinuum_h2_target()
    msg = f"Unknown Quantinuum device: {device_name}"
    raise ValueError(msg)


def get_quantinuum_h2_target() -> Target:
    """Get the target device for Quantinuum H2."""
    num_qubits = 56
    connectivity = [[a, b] for a in range(num_qubits) for b in range(num_qubits) if a != b]
    return _build_quantinuum_target(
        name="quantinuum_h2",
        num_qubits=num_qubits,
        connectivity=connectivity,
        oneq_error=0.00003,
        twoq_error=0.0015,
        spam_error=0.0015,
    )


def _build_quantinuum_target(
    name: str,
    num_qubits: int,
    connectivity: list[list[int]],
    oneq_error: float,
    twoq_error: float,
    spam_error: float,
) -> Target:
    """Construct a hardcoded Quantinuum target using mean values."""
    target = Target(num_qubits=num_qubits, description=name)

    # Define symbolic parameters
    theta = Parameter("theta")
    phi = Parameter("phi")
    alpha = Parameter("alpha")

    # === Add single-qubit gates ===
    single_qubit_gate_props = {(q,): InstructionProperties(error=oneq_error) for q in range(num_qubits)}
    measure_props = {(q,): InstructionProperties(error=spam_error) for q in range(num_qubits)}

    target.add_instruction(RXGate(theta), single_qubit_gate_props)
    target.add_instruction(RYGate(phi), single_qubit_gate_props)
    target.add_instruction(RZGate(theta), single_qubit_gate_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit RZZ gates ===
    rzz_props = {(q1, q2): InstructionProperties(error=twoq_error) for q1, q2 in connectivity}
    target.add_instruction(RZZGate(alpha), rzz_props)

    return target
