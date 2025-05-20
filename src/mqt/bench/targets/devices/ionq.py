# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the IonQ calibration data."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RXGate, RXXGate, RYGate, RZGate
from qiskit.transpiler import InstructionProperties, Target


def get_ionq_target(device_name: str) -> Target:
    """Get the target device for a given IonQ device name."""
    if device_name == "ionq_aria1":
        return get_ionq_aria1_target()
    if device_name == "ionq_harmony":
        return get_ionq_harmony_target()
    msg = f"Unknown IonQ device: {device_name}"
    raise ValueError(msg)


def get_ionq_aria1_target() -> Target:
    """Get the target device for IonQ Aria1."""
    return _build_ionq_target(
        num_qubits=25,
        description="ionq_aria1",
        oneq_duration=135e-6,
        twoq_duration=600e-6,
        readout_duration=300e-6,
        oneq_fidelity=0.9829,
        twoq_fidelity=0.996,
        spam_fidelity=0.9993,
    )


def get_ionq_harmony_target() -> Target:
    """Get the target device for IonQ Harmony."""
    return _build_ionq_target(
        num_qubits=11,
        description="ionq_harmony",
        oneq_duration=10e-6,
        twoq_duration=200e-6,
        readout_duration=130e-6,
        oneq_fidelity=0.9985,
        twoq_fidelity=0.9614,
        spam_fidelity=0.99752,
    )


def _build_ionq_target(
    *,
    num_qubits: int,
    description: str,
    oneq_duration: float,
    twoq_duration: float,
    readout_duration: float,
    oneq_fidelity: float,
    twoq_fidelity: float,
    spam_fidelity: float,
) -> Target:
    """Construct an IonQ target with all-to-all connectivity and parametric gates."""
    target = Target(description=description)

    # Parameters for parametric gates
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")
    alpha = Parameter("alpha")

    # Define basis gates
    rx_gate = RXGate(theta)
    ry_gate = RYGate(phi)
    rz_gate = RZGate(lam)
    rxx_gate = RXXGate(alpha)
    measure_gate = Measure()

    # Add single-qubit gates
    target.add_instruction(
        rx_gate,
        {(q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)},
    )
    target.add_instruction(
        ry_gate,
        {(q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)},
    )
    target.add_instruction(rz_gate, {(q,): InstructionProperties(duration=0.0, error=0.0) for q in range(num_qubits)})
    target.add_instruction(
        measure_gate,
        {(q,): InstructionProperties(duration=readout_duration, error=1 - spam_fidelity) for q in range(num_qubits)},
    )

    # Add two-qubit gates (all-to-all connectivity)
    target.add_instruction(
        rxx_gate,
        {
            (q1, q2): InstructionProperties(duration=twoq_duration, error=1 - twoq_fidelity)
            for q1 in range(num_qubits)
            for q2 in range(num_qubits)
            if q1 != q2
        },
    )

    return target
