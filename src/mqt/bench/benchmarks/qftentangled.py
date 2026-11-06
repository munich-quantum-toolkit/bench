# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""QFT entangled benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate

from ._registry import register_benchmark


@register_benchmark("qftentangled", description="QFT with GHZ state input")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Apply the quantum Fourier transform to a GHZ state.

    Args:
        num_qubits: Number of qubits in the GHZ state and the transform.

    Returns:
        A circuit that measures the full register after the transform.
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q)
    qc.h(q[-1])
    for i in range(1, num_qubits):
        qc.cx(q[num_qubits - i], q[num_qubits - i - 1])

    qc.compose(QFTGate(num_qubits=num_qubits), inplace=True)

    qc.measure_all()
    qc.name = "qftentangled"

    return qc
