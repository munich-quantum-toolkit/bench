# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Grover benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import grover_operator

from ._registry import register_benchmark


@register_benchmark("grover", description="Grover's Algorithm")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing Grover's algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    num_qubits = num_qubits - 1  # -1 because of the flag qubit
    q = QuantumRegister(num_qubits, "q")
    flag = AncillaRegister(1, "flag")

    state_preparation = QuantumCircuit(q, flag)
    state_preparation.h(q)
    state_preparation.x(flag)

    oracle = QuantumCircuit(q, flag)
    oracle.mcp(np.pi, q, flag)

    operator = grover_operator(oracle)
    iterations = int(np.pi / 4 * np.sqrt(2**num_qubits))

    num_qubits = operator.num_qubits - 1  # -1 because last qubit is "flag" qubit and already taken care of

    # num_qubits may differ now depending on the mcx_mode
    q2 = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q2, flag, name="grover")
    qc.compose(state_preparation, inplace=True)

    qc.compose(operator.power(iterations), inplace=True)
    qc.measure_all()
    qc.name = qc.name

    return qc
