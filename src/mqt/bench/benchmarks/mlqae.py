# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Maximum Likelihood Quantum Amplitude estimation benchmark definition. Code is based on the paper Suzuki et al.,: Amplitude Estimation without Phase Estimation (2020): https://arxiv.org/abs/1904.10246."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, ForLoopOp, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import grover_operator

from ._registry import register_benchmark


@register_benchmark("mlqae", description="Maximum Likelihood Quantum Amplitude Estimation")
def create_circuit(
    num_qubits: int, num_rounds: int = 3, b_max: float = np.pi / 4, *, for_loop: bool = False
) -> QuantumCircuit:
    """Returns a quantum circuit implementing the quantum part of ML-QAE.

    The circuit is based on Section 4.2 of the paper. The circuit follows the fixed exponentially increasing schedule: round 0 applies A only,
    round k (k = 1...num_rounds) applies ``Q^(2^(k-1))`` after A. Each round's result is stored in its own classical bit and all qubits are reset between rounds. The classical maximum-likelihood post-processing is not part of the circuit.

    Arguments:
        num_qubits: Total number of qubits (state qubits + 1 objective qubit). Must be at least 1.
        num_rounds: Number of Grover-amplified rounds (in addition to the m = 0 round). Must be at least 1.
        b_max: Upper limit of the integral.
        for_loop: Whether to use a structured for-loop for the Grover iterations within each round.

    Returns:
        QuantumCircuit: The constructed ML-QAE circuit.
    """
    if num_rounds < 1:
        msg = "num_rounds must be at least 1."
        raise ValueError(msg)

    if b_max <= 0:
        msg = "b_max must be positive."
        raise ValueError(msg)
    
    objective = num_qubits - 1
    num_state_qubits = objective

    # State preparation A (Sec. 4.2, Fig. 5): Hadamards create the uniform distribution on the state qubits,
    # and controlled Y-rotations rotate the objective qubit
    state_preparation = QuantumCircuit(num_qubits, name="A")
    if objective > 0:
        state_preparation.h(range(num_state_qubits))
    state_preparation.ry(b_max / 2**num_state_qubits, objective)
    for j in range(num_state_qubits):
        state_preparation.cry(2 ** (j + 1) * b_max / 2**num_state_qubits, j, objective)

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
