# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Graphstate benchmark definition."""

from __future__ import annotations

import networkx as nx
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("graphstate", description="Graph State")
def create_circuit(num_qubits: int, degree: int = 2, seed: int | None = None) -> QuantumCircuit:
    """Prepare the graph state of a random regular graph.

    Args:
        num_qubits: Number of vertices, one per qubit.
        degree: Edges per vertex. Must satisfy ``0 <= degree < num_qubits``, with
            ``num_qubits * degree`` even.
        seed: Seed for the graph generator. Use an integer to reproduce the graph.

    Returns:
        A circuit with one CZ gate per edge and a final measurement of every qubit.
    """
    if not 0 <= degree < num_qubits or num_qubits * degree % 2:
        msg = "degree must satisfy 0 <= degree < num_qubits, and num_qubits * degree must be even."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="graphstate")

    g = nx.random_regular_graph(degree, num_qubits, seed=seed)
    # Keep NetworkX's node order to preserve seeded wire assignments.
    indices = {node: index for index, node in enumerate(g)}
    edges = sorted(sorted((indices[a], indices[b])) for a, b in g.edges)
    qc.h(q)
    for a, b in edges:
        qc.cz(a, b)
    qc.measure_all()
    return qc
