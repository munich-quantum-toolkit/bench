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
    """HHL algorithm for a fixed 2x2 Hermitian matrix A using scalable QPE precision.

    Args:
        num_qubits: Number of qubits in the phase estimation register (precision control)

    Returns:
        QuantumCircuit: Qiskit circuit implementing HHL
    """
    # Registers:
    qr_sys = QuantumRegister(1, name="sys")  # System qubit (|b⟩)
    qr_eig = QuantumRegister(num_qubits, name="phase")  # Eigenvalue estimation
    qr_anc = QuantumRegister(1, name="ancilla")  # Ancilla for rotation
    cr = ClassicalRegister(1, name="c")  # Classical for system measurement
    qc = QuantumCircuit(qr_sys, qr_eig, qr_anc, cr)

    # Step 1: Prepare |b⟩ = |0⟩ + no gates (b = [1, 0])
    # (Optionally use other b if desired)

    # Step 2: Apply Hadamards to phase register (QPE start)
    qc.h(qr_eig)

    # Step 3: Simulate controlled-evolution (U = e^{iAt})
    # Eigenvalues of A are known: λ1 ≈ 0.38, λ2 ≈ 3.62
    # Eigenvectors: we can diagonalize A as V† D V
    # So we simulate the effect of exp(i A t) ≈ V† exp(i D t) V
    #
    # For a fixed A and small system, we simulate controlled unitaries with known eigenvalues

    # Evolution time
    t = 2 * np.pi

    # Eigenvalues of A (diagonal)
    lambdas = [0.381966, 3.6180]

    # Simulate controlled-U^2^j for each phase qubit
    for j in range(num_qubits):
        # Controlled rotation that approximates controlled-evolution
        angle = t * lambdas[1] / (2 ** (j + 1))  # simulate highest eigenvalue
        qc.cp(angle, qr_sys[0], qr_eig[j])

    # Step 4: Apply inverse QFT
    qc.append(QFTGate(num_qubits).inverse(), qr_eig)

    # Step 5: Controlled Ry rotations on ancilla (1/λ scaling)
    for j in range(num_qubits):
        # Simulate λ ≈ 2^j encoded in binary QPE
        lambda_j = 2**j  # fake lambda to match QPE index
        theta = 2 * np.arcsin(1.0 / lambda_j)
        qc.cry(theta, qr_eig[j], qr_anc[0])

    # Step 6: QPE uncomputation (apply QFT + unitaries again)
    qc.append(QFTGate(num_qubits), qr_eig)
    for j in reversed(range(num_qubits)):
        angle = -t * lambdas[1] / (2 ** (j + 1))
        qc.cp(angle, qr_sys[0], qr_eig[j])
    qc.h(qr_eig)

    # Step 7: Measure the system register
    qc.measure(qr_sys[0], cr[0])
    qc.name = "hhl"
    return qc
