# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Graphstate benchmark definition."""

from __future__ import annotations

import networkx as nx
from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import GraphStateGate

from ._registry import register_benchmark


@register_benchmark("graphstate", description="Graph State")
def create_circuit(num_qubits: int, degree: int = 2) -> QuantumCircuit:
    """Returns a quantum circuit implementing a graph state.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        degree: number of edges per node
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="graphstate")

    g = nx.random_regular_graph(degree, num_qubits)
    a = nx.convert_matrix.to_numpy_array(g)
    qc.compose(GraphStateGate(a), inplace=True)
    qc.measure_all()
    return qc.decompose(gates_to_decompose="graph_state")
