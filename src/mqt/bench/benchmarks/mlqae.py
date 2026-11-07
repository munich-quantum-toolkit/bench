# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Maximum Likelihood Quantum Amplitude Estimation benchmark definition.

Based on Suzuki et al., "Amplitude Estimation without Phase Estimation" (2020).
https://arxiv.org/abs/1904.10246
"""

from __future__ import annotations

import math

import numpy as np
from qiskit.circuit import ClassicalRegister, ForLoopOp, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import grover_operator

from ._registry import register_benchmark


@register_benchmark("mlqae", description="Maximum Likelihood Quantum Amplitude Estimation")
def create_circuit(
    num_qubits: int, num_rounds: int = 3, b_max: float = np.pi / 4, *, for_loop: bool = False
) -> QuantumCircuit:
    r"""Build the measurement circuit for maximum-likelihood amplitude estimation.

    The schedule in Sec. 4.2 of Suzuki et al. (https://arxiv.org/abs/1904.10246)
    starts with state preparation alone. Round :math:`k \geq 1` applies
    :math:`2^{k-1}` Grover iterations after state preparation. The circuit resets
    all qubits between rounds.

    Args:
        num_qubits: Total width, including one objective qubit. Must be at least 1.
        num_rounds: Number of amplified rounds after the unamplified round. Must be at least 1.
        b_max: Upper integration limit. Must be positive and finite.
        for_loop: Use a structured loop for the Grover iterations within each round.

    Returns:
        A circuit that records the objective qubit for round ``k`` in classical bit ``k``.
        The maximum-likelihood fit is a separate classical step.
    """
    if num_rounds < 1:
        msg = "num_rounds must be at least 1."
        raise ValueError(msg)

    if not np.isfinite(b_max) or b_max <= 0:
        msg = "b_max must be positive and finite."
        raise ValueError(msg)

    objective = num_qubits - 1
    num_state_qubits = objective

    # State preparation A (Sec. 4.2, Fig. 5): Hadamards create the uniform distribution on the state qubits,
    # and controlled Y-rotations rotate the objective qubit
    state_preparation = QuantumCircuit(num_qubits, name="A")
    if objective > 0:
        state_preparation.h(range(num_state_qubits))
    state_preparation.ry(math.ldexp(b_max, -num_state_qubits), objective)
    for j in range(num_state_qubits):
        angle = math.ldexp(b_max, j + 1 - num_state_qubits)
        state_preparation.cry(angle, j, objective)

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
