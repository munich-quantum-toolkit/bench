# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dynamical QFT benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit import ClassicalRegister
from qiskit.circuit import QuantumCircuit, QuantumRegister

from ._registry import register_benchmark

@register_benchmark("dynamic_qft", description="Dynamic QFT")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Return a circuit implementing the Dynamic QFT."""
    if num_qubits < 1:
        msg = "The number of qubits must be at least 1."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")

    # Forward loop that mirrors the gate order and qubit indices of the static QFT
    for i in range(num_qubits):
        qc.h(q[i])
        qc.measure(q[i], c[i])

        # Apply feed-forward phase corrections to all remaining qubits
        for j in range(i + 1, num_qubits):
            angle = np.pi / (2 ** (j - i))
            qc.p(angle, q[j]).c_if(c[i], 1)

    return qc
