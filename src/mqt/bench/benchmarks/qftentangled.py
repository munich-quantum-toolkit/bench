# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
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
    """Returns a quantum circuit implementing the Quantum Fourier Transform algorithm using entangled qubits.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the Quantum Fourier Transform algorithm using entangled qubits
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
