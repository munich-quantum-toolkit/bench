# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dynamic QFT benchmark definition."""

from __future__ import annotations

import math

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("dynamic_qft", description="Dynamic QFT")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Return a circuit implementing the Dynamic QFT.

    This benchmark follows the semiclassical Quantum Fourier Transform by
    Griffiths and Niu. Each qubit is transformed with a Hadamard gate, measured
    immediately, and then its classical result controls phase rotations on the
    remaining qubits. This replaces the usual controlled-phase gates with
    mid-circuit measurements and classical feed-forward while keeping the same
    triangular phase-angle structure as the standard QFT.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit.

    Returns:
        QuantumCircuit: a quantum circuit implementing the Dynamic QFT.
    """
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")

    for measured_qubit in range(num_qubits):
        measured_bit = num_qubits - measured_qubit - 1
        qc.h(q[measured_qubit])
        qc.measure(q[measured_qubit], c[measured_bit])

        for offset in range(1, num_qubits - measured_qubit):
            with qc.if_test((c[measured_bit], 1)):
                qc.p(math.pi / (2**offset), q[measured_qubit + offset])

    return qc
