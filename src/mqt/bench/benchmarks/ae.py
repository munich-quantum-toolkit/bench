# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Amplitude estimation benchmark definition. Code is based on https://qiskit.org/documentation/finance/tutorials/00_amplitude_estimation.html."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import phase_estimation

from ._registry import register_benchmark


@register_benchmark("ae", description="Amplitude Estimation")
def create_circuit(num_qubits: int, probability: float = 0.2) -> QuantumCircuit:
    """Returns a quantum circuit implementing Quantum Amplitude Estimation.

    Arguments:
        num_qubits: Total number of qubits, including evaluation and target qubits.
        probability: Probability of the "good" state.

    Returns:
        QuantumCircuit: The constructed amplitude estimation circuit.
    """
    if num_qubits < 2:
        msg = "Number of qubits must be at least 2 (1 evaluation + 1 target)."
        raise ValueError(msg)

    # Compute the rotation angle: theta_p = 2 * arcsin(sqrt(p))
    theta_p = 2 * np.arcsin(np.sqrt(probability))

    # Create the state-preparation operator (A operator) as a single-qubit circuit.
    state_preparation = QuantumCircuit(1)
    state_preparation.ry(theta_p, 0)

    # Create the Grover operator (Bernoulli Q operator) as a single-qubit circuit.
    # It applies a rotation of 2 * theta_p, which corresponds to an effective rotation of 4*arcsin(sqrt(p)).
    grover_operator = QuantumCircuit(1)
    grover_operator.ry(2 * theta_p, 0)

    # Compute the number of evaluation qubits (phase estimation qubits).
    num_eval_qubits = num_qubits - 1

    # Build the phase estimation circuit with the specified number of evaluation qubits and the Grover operator.
    pe = phase_estimation(num_eval_qubits, grover_operator)

    # Create the overall circuit using the quantum registers from the phase estimation circuit.
    qc = QuantumCircuit(*pe.qregs)

    # Compose the state-preparation operator on the target qubit. We assume that the target qubit
    # is the last qubit in the register list.
    qc.compose(state_preparation, list(range(num_eval_qubits, qc.num_qubits)), inplace=True)

    # Compose the phase estimation component.
    qc.compose(pe.decompose(gates_to_decompose="unitary"), inplace=True)

    # Name the circuit and add measurements to all evaluation qubits.
    qc.name = "ae"
    qc.measure_all()

    return qc
