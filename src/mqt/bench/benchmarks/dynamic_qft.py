# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dynamic QFT benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("dynamic_qft", description="Dynamic Quantum Fourier Transformation and Measurement (DQFT + M)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Dynamic Quantum Fourier Transform and Measurement algorithm, where the measurement outcomes are the classical control of the subsequent phase gates. The circuit consists of a sequence of Hadamard gates, measurements, and classically controlled phase gates and is based on the circuit described in Phys. Rev. Lett. 133, 150602 (2024).

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit. Must be ≤ 60.

    Returns:
        QuantumCircuit: a quantum circuit implementing the Dynamic Quantum Fourier Transform and Measurement algorithm
    """
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")
    for i in range(num_qubits):
        qc.h(q[i])
        qc.measure(q[i], c[i])
        with qc.if_test((c[i], 1)):
            for j in range(1, num_qubits - i):
                qc.p(np.pi / 2**j, q[j + i])
    return qc
