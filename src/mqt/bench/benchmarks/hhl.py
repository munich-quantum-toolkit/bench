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
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate

from ._registry import register_benchmark


@register_benchmark("hhl", description="Harrow-Hassidim-Lloyd Algorithm (HHL)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """HHL algorithm for a fixed 2x2 Hermitian matrix A using scalable QPE precision.

    This implementation simulates a more accurate model of the HHL algorithm
    for the matrix A = [[1, 1], [1, 3]] with known eigenvalues.

    Args:
        num_qubits: Number of qubits in the phase estimation register (precision control)

    Returns:
        QuantumCircuit: Qiskit circuit implementing HHL
    """
    assert num_qubits >= 3, "Number of qubits must be at least 3 for HHL."
    num_qpe_qubits = num_qubits - 2
    qr_sys = QuantumRegister(1, name="sys")  # System qubit (|b⟩)
    qr_eig = QuantumRegister(num_qpe_qubits, name="phase")  # Eigenvalue estimation
    qr_anc = QuantumRegister(1, name="ancilla")  # Ancilla for rotation
    cr = ClassicalRegister(1, name="c")  # Classical for system measurement
    qc = QuantumCircuit(qr_sys, qr_eig, qr_anc, cr)

    # Step 1: Prepare |b⟩ = |1⟩
    qc.x(qr_sys[0])

    # Step 2: Apply Hadamards to phase register (QPE start)
    qc.h(qr_eig)

    # Step 3: Controlled-unitary approximation simulating controlled-e^{iAt}
    # A = [[1, 1], [1, 3]], eigenvalues: lam1 ≈ 0.382, lam2 ≈ 3.618
    # We simulate one eigenvalue's evolution as approximation
    t = 2 * np.pi
    lam = 3.618  # simulate dominant eigenvalue for better realism

    for j in range(num_qpe_qubits):
        angle = t * lam / (2 ** (j + 1))
        qc.cp(angle, qr_eig[j], qr_sys[0])

    # Step 4: Apply inverse QFT
    qc.append(QFTGate(num_qpe_qubits).inverse(), qr_eig)

    # Step 5: Controlled Ry rotations on ancilla (based on actual eigenvalue)
    for j in range(num_qpe_qubits):
        # Approximate eigenvalue encoded in basis state |j⟩
        # Use inverse λ (scaled appropriately)
        estimated_lambda = lam / (2 ** (num_qpe_qubits - j))
        if estimated_lambda > 0:
            inv_lambda = 1.0 / estimated_lambda
            inv_lambda = np.clip(inv_lambda, -1, 1)  # valid for arcsin
            theta = 2 * np.arcsin(inv_lambda)
            qc.cry(theta, qr_eig[j], qr_anc[0])

    # Step 6: QPE uncomputation (apply QFT + reverse controlled unitary)
    qc.append(QFTGate(num_qpe_qubits), qr_eig)
    for j in reversed(range(num_qpe_qubits)):
        angle = -t * lam / (2 ** (j + 1))
        qc.cp(angle, qr_eig[j], qr_sys[0])

    # Step 7: Final Hadamards and measurement
    qc.h(qr_eig)
    qc.measure(qr_sys[0], cr[0])
    qc.name = "hhl"
    return qc
