# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Maximum Likelihood Quantum Amplitude estimation benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, ForLoopOp, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import grover_operator

from ._registry import register_benchmark


@register_benchmark("mlqae", description="Maximum Likelihood Quantum Amplitude Estimation")
def create_circuit(num_qubits: int, num_rounds: int = 3, probability: float = 0.2, *, for_loop: bool = False) -> QuantumCircuit:
    """Returns a quantum circuit implementing the quantum part of ML-QAE.

    Arguments:
        num_qubits: Total number of qubits (state qubits + 1 objective qubit). Must be at least 1.
        num_rounds: Number of Grover-amplified rounds (in addition to the m = 0 round). Must be at least 1.
        probability: Probability of the "good" state (objective qubit measured as 1).
        for_loop: Whether to use a structured for-loop for the Grover iterations within each round.

    Returns:
        QuantumCircuit: The constructed ML-QAE circuit.
    """
    if num_rounds < 1:
        msg = "num_rounds must be at least 1."
        raise ValueError(msg)
    if not 0 <= probability <= 1:
        msg = "probability must be in [0, 1]."
        raise ValueError(msg)

    # Compute the rotation angle: theta_p = 2 * arcsin(sqrt(p))
    theta_p = 2 * np.arcsin(np.sqrt(probability))

    objective = num_qubits - 1

    # State preparation A: uniform superposition on the state qubits, Bernoulli(p) on the objective qubit.
    state_preparation = QuantumCircuit(num_qubits, name="A")
    if objective > 0:
        state_preparation.h(range(objective))
    state_preparation.ry(theta_p, objective)

    # Oracle marking the good state (objective = 1) and Grover operator Q = A S_0 A^dagger S_chi.
    oracle = QuantumCircuit(num_qubits, name="S_chi")
    oracle.z(objective)
    operator = grover_operator(oracle, state_preparation=state_preparation)

    # Fixed schedule m_0 = 0, m_k = 2^(k-1).
    schedule = [0] + [2**k for k in range(num_rounds)]

    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(len(schedule), "c")
    qc = QuantumCircuit(q, c, name="mlqae")

    for k, m_k in enumerate(schedule):
        qc.compose(state_preparation, q, inplace=True)

        if m_k > 0:
            if for_loop:
                body = QuantumCircuit(q)
                body.append(operator.to_gate(), body.qubits)
                qc.append(ForLoopOp(range(m_k), None, body), qc.qubits)
            else:
                qc.compose(operator.power(m_k), q, inplace=True)

        qc.measure(q[objective], c[k])

        # Reset the working qubits if more rounds are needed
        if k < len(schedule) - 1:
            qc.reset(q)

    return qc
