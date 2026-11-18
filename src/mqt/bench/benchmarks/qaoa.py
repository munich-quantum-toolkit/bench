# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""QAOA benchmark definition. Code is based on https://github.com/qiskit-community/qiskit-application-modules-demo-sessions/blob/main/qiskit-optimization/qiskit-optimization-demo.ipynb."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ParameterVector, QuantumCircuit

from ._registry import register_benchmark


@register_benchmark("qaoa", description="Quantum Approximate Optimization Algorithm (QAOA)")
def create_circuit(num_qubits: int, repetitions: int = 2, seed: int = 10) -> QuantumCircuit:
    """Build a QAOA ansatz for Max-Cut on a random graph.

    Args:
        num_qubits: Number of vertices, one per qubit.
        repetitions: Number of cost and mixer layers. Must be nonnegative.
        seed: Seed for generating the graph.

    Returns:
        A circuit with symbolic rotation angles. Each measured bit assigns one vertex to a side of the cut.
    """
    if repetitions < 0:
        msg = "repetitions must be nonnegative."
        raise ValueError(msg)

    rng = np.random.default_rng(seed)
    adjacency_matrix = rng.integers(0, 2, size=(num_qubits, num_qubits))
    edge_starts, edge_ends = (indices.tolist() for indices in np.triu(adjacency_matrix, 1).nonzero())

    gamma_values = ParameterVector("g", repetitions)
    beta_values = ParameterVector("b", repetitions)

    qc = QuantumCircuit(num_qubits, name="qaoa")
    qc.h(range(num_qubits))
    for layer in range(repetitions):
        if edge_starts:
            qc.rzz(2 * gamma_values[layer], edge_starts, edge_ends)
        qc.rx(2 * beta_values[layer], range(num_qubits))

    qc.measure_all()
    return qc
