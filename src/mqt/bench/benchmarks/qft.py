# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""QFT benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate

from ._registry import register_benchmark


@register_benchmark("qft", description="Quantum Fourier Transformation (QFT)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Quantum Fourier Transform algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the Quantum Fourier Transform algorithm
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="qft")
    qc.compose(QFTGate(num_qubits=num_qubits), inplace=True)
    qc.measure_all()

    return qc
