# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""HHL Benchmark Circuit Generation."""

from __future__ import annotations

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate


def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Creates a simplified HHL circuit for a fixed tridiagonal matrix with known eigenvalues.

    Arguments:
        num_qubits: Number of qubits representing the system size (2**num_qubits system)

    Returns:
        QuantumCircuit implementing the simplified HHL algorithm.
    """
    # Allocate quantum registers:
    # - 1 ancilla qubit for rotation
    # - num_qubits for eigenvalue register (QPE)
    # - num_qubits for system register (represents |b>)
    qr_anc = QuantumRegister(1, "anc")
    qr_eig = QuantumRegister(num_qubits, "eig")
    qr_sys = QuantumRegister(num_qubits, "sys")
    cr = ClassicalRegister(num_qubits + 1, "c")
    qc = QuantumCircuit(qr_anc, qr_eig, qr_sys, cr)

    # Step 1: Prepare initial state |b⟩
    # For simplicity, we choose |b⟩ = |1,0,...,0> → x gate on the first qubit
    qc.x(qr_sys[0])

    # Step 2: Apply Hadamard to eigenvalue register to create uniform superposition
    qc.h(qr_eig)

    # Step 3: Simulate controlled-evolution e^{iAt} (for known eigenvalues)
    # In real HHL, this would be controlled-U operations based on A
    # Here we simulate with controlled-phase shifts as placeholders
    for i in range(num_qubits):
        qc.cp(2 * np.pi / (2 ** (i + 1)), qr_sys[0], qr_eig[i])

    # Step 4: Apply inverse QFT to eigenvalue register to "extract" eigenvalues
    qc.append(QFTGate(num_qubits).inverse(), qr_eig)

    # Step 5: Perform controlled rotation on the ancilla, based on estimated eigenvalues
    # These rotations simulate the 1/λ scaling used to construct A^{-1}|b>
    for i in range(num_qubits):
        theta = 2 * np.arcsin(1 / (2 ** (i + 1)))  # simulate θ = arcsin(1/λ)
        qc.cry(theta, qr_eig[i], qr_anc[0])

    # Step 6: Uncompute QPE by reversing the QPE steps
    qc.append(QFTGate(num_qubits), qr_eig)
    for i in reversed(range(num_qubits)):
        qc.cp(-2 * np.pi / (2 ** (i + 1)), qr_sys[0], qr_eig[i])
    qc.h(qr_eig)

    # Step 7: Measurement
    qc.measure(qr_sys[0], cr[0])  # Measure one system qubit (could also use all)
    for i in range(num_qubits):
        qc.measure(qr_eig[i], cr[i + 1])  # Measure eigenvalue register

    qc.name = "hhl"
    return qc
