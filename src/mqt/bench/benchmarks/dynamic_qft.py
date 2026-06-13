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


@register_benchmark("dynamic_qft", description="Dynamical Quantum Fourier Transformation (DQFT)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Dynamic Quantum Fourier Transform algorithm,
    using mid-circuit measurements and classical feed-forward loops.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the Dynamic Quantum Fourier Transform algorithm
    """
    if num_qubits < 1:
        msg = "The number of qubits must be at least 1."
        raise ValueError(msg)

    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")

    # Semiclassical QFT must step backward from the most significant bit down to 0
    for i in reversed(range(num_qubits)):
        _handle_dynamic_qft_qubit(qc, q, c, i)

    return qc


def _apply_single_qubit_rotations(
    qc: QuantumCircuit, q: QuantumRegister, c: ClassicalRegister, target_idx: int
) -> None:
    """This function scans previously measured bits and applies conditional phase gates to the target qubit,.

    based on the classical measurement outcomes of all preceding qubits.
    """
    num_qubits = len(q)

    # Scan all qubits that have already been processed and measured (j > target_idx)
    for j in range(target_idx + 1, num_qubits):
        # Semiclassical phase angle: θ = π / 2^(j - target_idx)
        angle = np.pi / (2 ** (j - target_idx))

        # Condition the phase gate directly on the individual classical bit
        with qc.if_test((c[j], 1)):
            qc.p(angle, q[target_idx])


def _handle_dynamic_qft_qubit(qc: QuantumCircuit, q: QuantumRegister, c: ClassicalRegister, qubit_idx: int) -> None:
    """This function applies the full dynamical step for a single qubit:

    1. Applies feed-forward phase corrections from past measurements.
    2. Shifts to the transverse basis via a Hadamard gate.
    3. Triggers an immediate mid-circuit measurement.

    """
    # 1. Compute phase rotations from previously measured qubits
    _apply_single_qubit_rotations(qc, q, c, qubit_idx)

    # 2. Rotate the basis
    qc.h(q[qubit_idx])

    # 3. Collapse the state into the classical register
    qc.measure(q[qubit_idx], c[qubit_idx])
