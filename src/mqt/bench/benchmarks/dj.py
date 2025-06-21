# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Deutsch Josza benchmark definition. Code is based on https://qiskit.org/textbook/ch-algorithms/deutsch-jozsa.html."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit

from ._registry import register_benchmark


def dj_oracle(case: str, n: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Deutsch-Josza oracle."""
    # plus one output qubit
    oracle_qc = QuantumCircuit(n + 1)
    rng = np.random.default_rng(10)

    if case == "balanced":
        b_str = ""
        for _ in range(n):
            b = rng.integers(0, 2)
            b_str = b_str + str(b)

        for qubit in range(len(b_str)):
            if b_str[qubit] == "1":
                oracle_qc.x(qubit)

        for qubit in range(n):
            oracle_qc.cx(qubit, n)

        for qubit in range(len(b_str)):
            if b_str[qubit] == "1":
                oracle_qc.x(qubit)

    if case == "constant":
        output = rng.integers(2)
        if output == 1:
            oracle_qc.x(n)

    oracle_gate = oracle_qc.to_gate()
    oracle_gate.name = "Oracle"  # To show when we display the circuit
    return oracle_gate


def dj_algorithm(oracle: QuantumCircuit, n: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Deutsch-Josza algorithm."""
    dj_circuit = QuantumCircuit(n + 1, n)

    dj_circuit.x(n)
    dj_circuit.h(n)

    for qubit in range(n):
        dj_circuit.h(qubit)

    dj_circuit.append(oracle, range(n + 1))

    for qubit in range(n):
        dj_circuit.h(qubit)

    dj_circuit.barrier()
    for i in range(n):
        dj_circuit.measure(i, i)

    return dj_circuit


@register_benchmark("dj", description="Deutsch-Jozsa")
def create_circuit(num_qubits: int, balanced: bool = True) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Deutsch-Josza algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        balanced: True for a balanced and False for a constant oracle
    """
    oracle_mode = "balanced" if balanced else "constant"
    num_qubits = num_qubits - 1  # because of ancilla qubit
    oracle_gate = dj_oracle(oracle_mode, num_qubits)
    qc = dj_algorithm(oracle_gate, num_qubits)
    qc.name = "dj"

    return qc
