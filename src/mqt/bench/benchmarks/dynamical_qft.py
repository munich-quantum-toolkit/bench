# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# QFT & M v.1

"""Dynamical QFT + M benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("dynamical_qft", description="Dynamic Quantum Fourier Transformation and Measurement (DQFT + M)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Dynamic Quantum Fourier Transform and Measurement algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the Dynamic Quantum Fourier Transform and Measurement algorithm
    """
    q = QuantumRegister(num_qubits, "q")
    cl = ClassicalRegister(num_qubits, "cl")
    qc = QuantumCircuit(q, cl, name="dynamical_qft")
    for i in range(num_qubits):
        qc.h(q[i])
        qc.measure(q[i], cl[i])
        with qc.if_test((cl[i], 1)):
            for j in range(1, num_qubits - i):
                qc.p(2 * np.pi / 2 ** (j + 1), q[j + i])
    return qc
