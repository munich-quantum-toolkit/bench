# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Qwalk benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("qwalk", description="Quantum Walk")
def create_circuit(
    num_qubits: int,
    depth: int = 3,
    coin_state_preparation: QuantumCircuit | None = None,
) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Quantum Walk algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: number of quantum steps
        coin_state_preparation: optional quantum circuit for state preparation
        ancillary_mode: defining the decomposition scheme

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

    for _ in range(depth):
        # Hadamard coin operator
        qc.h(coin)

        # controlled increment
        for i in range(num_qubits - 1):
            qc.mcx(coin[:] + node[i + 1 :], node[i])
        qc.cx(coin, node[num_qubits - 1])

        # controlled decrement
        qc.x(coin)
        qc.x(node[1:])
        for i in range(num_qubits - 1):
            qc.mcx(coin[:] + node[i + 1 :], node[i])
        qc.cx(coin, node[num_qubits - 1])
        qc.x(node[1:])
        qc.x(coin)

    qc.measure_all()
    qc.name = qc.name

    return qc
