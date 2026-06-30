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


@register_benchmark("dynamic_qft", description="Dynamic Quantum Fourier Transformation (QFT)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Dynamic Quantum Fourier Transform algorithm.

    More details on the “Semiclassical Fourier Transform for Quantum Computation” can be seen in https://arxiv.org/abs/quant-ph/9511007

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the Dynamic Quantum Fourier Transform algorithm
    """
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")

    # Mirror index order of regular "qft" benchmark
    for qubit in reversed(range(num_qubits)):
        bit = num_qubits - qubit - 1
        qc.h(q[qubit])
        qc.measure(q[qubit], c[bit])

        for target in reversed(range(qubit)):
            with qc.if_test((c[bit], 1)):
                qc.p(np.pi * (2.0 ** (target - qubit)), q[target])

    return qc
