# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Qwalk benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ForLoopOp, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("qwalk", description="Quantum Walk")
def create_circuit(
    num_qubits: int,
    depth: int = 3,
    coin_state_preparation: QuantumCircuit | None = None,
    *,
    for_loop: bool = False,
) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Quantum Walk algorithm.

    Args:
        num_qubits: number of qubits of the returned quantum circuit
        depth: number of quantum steps
        coin_state_preparation: optional quantum circuit for state preparation
        for_loop: whether to use a structured for-loop for the quantum walk steps

    Returns:
        qc: a quantum circuit implementing the Quantum Walk algorithm
    """
    num_qubits = num_qubits - 1  # because one qubit is needed for the coin
    coin = QuantumRegister(1, "coin")
    node = QuantumRegister(num_qubits, "node")

    qc = QuantumCircuit(node, coin, name="qwalk")

    # coin state preparation
    if coin_state_preparation is not None:
        qc.append(coin_state_preparation, coin[:])

    walk = QuantumCircuit(node, coin) if for_loop else qc
    for _ in range(1 if for_loop else depth):
        # Hadamard coin operator
        walk.h(coin)

        # controlled increment
        for i in range(num_qubits - 1):
            walk.mcx(coin[:] + node[i + 1 :], node[i])
        walk.cx(coin, node[num_qubits - 1])

        # controlled decrement
        walk.x(coin)
        walk.x(node[1:])
        for i in range(num_qubits - 1):
            walk.mcx(coin[:] + node[i + 1 :], node[i])
        walk.cx(coin, node[num_qubits - 1])
        walk.x(node[1:])
        walk.x(coin)

    if for_loop:
        qc.append(ForLoopOp(range(depth), None, walk), qc.qubits)

    qc.measure_all()
    qc.name = qc.name

    return qc
