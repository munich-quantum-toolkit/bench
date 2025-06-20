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
from qiskit.circuit.library import Measure, RZGate
from qiskit.transpiler import InstructionProperties, Target

from ..gatesets.ionq import GPI2Gate, GPIGate, MSGate, ZZGate
from ._registry import register_device


@register_device("ionq_aria_25")
def get_ionq_aria_25() -> Target:
    """Get the target device for IonQ Aria 1."""
    num_qubits = 25
    return _build_ionq_target(
        num_qubits=num_qubits,
        description="ionq_aria_25",
        entangling_gate="MS",
        oneq_duration=135e-6,
        twoq_duration=600e-6,
        readout_duration=300e-6,
        oneq_fidelity=0.9998,
        twoq_fidelity=0.98720,
        spam_fidelity=0.99370,
    )


@register_device("ionq_forte_36")
def get_ionq_forte_36() -> Target:
    """Get the target device for IonQ Forte 1."""
    num_qubits = 36
    return _build_ionq_target(
        num_qubits=num_qubits,
        description="ionq_forte_36",
        entangling_gate="ZZ",
        oneq_duration=130e-6,
        twoq_duration=970e-6,
        readout_duration=150e-6,
        oneq_fidelity=0.9998,
        twoq_fidelity=0.9932,
        spam_fidelity=0.9959,
    )


def _build_ionq_target(
    *,
    num_qubits: int,
    description: str,
    entangling_gate: str,
    oneq_duration: float,
    twoq_duration: float,
    readout_duration: float,
    oneq_fidelity: float,
    twoq_fidelity: float,
    spam_fidelity: float,
) -> Target:
    """Construct a hardcoded IonQ target using mean values."""
    target = Target(num_qubits=num_qubits, description=description)

    theta = Parameter("theta")
    phi = Parameter("phi")

    # === Add single-qubit gates ===
    singleq_props = {
        (q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)
    }
    rz_props = {(q,): InstructionProperties(duration=0, error=0) for q in range(num_qubits)}
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=1 - spam_fidelity) for q in range(num_qubits)
    }

    target.add_instruction(RZGate(theta), rz_props)
    target.add_instruction(GPIGate(theta), singleq_props)
    target.add_instruction(GPI2Gate(phi), singleq_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    connectivity = [(i, j) for i in range(num_qubits) for j in range(num_qubits) if i != j]
    twoq_props = {
        (q1, q2): InstructionProperties(duration=twoq_duration, error=1 - twoq_fidelity) for q1, q2 in connectivity
    }

    if entangling_gate == "MS":
        alpha = Parameter("alpha")
        beta = Parameter("beta")
        gamma = Parameter("gamma")
        target.add_instruction(MSGate(alpha, beta, gamma), twoq_props)
    elif entangling_gate == "ZZ":
        alpha = Parameter("alpha")
        target.add_instruction(ZZGate(alpha), twoq_props)
    else:
        msg = f"Unknown entangling gate: '{entangling_gate}'."
        raise ValueError(msg)
    return target
