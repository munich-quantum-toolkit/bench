# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
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
    """Build the quantum Fourier transform on the input register.

    Args:
        num_qubits: Number of qubits in the transform.

    Returns:
        A circuit with a computational-basis measurement on each output qubit.
    """
    q = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q, name="qft")
    qc.compose(QFTGate(num_qubits=num_qubits), inplace=True)
    qc.measure_all()

    return qc
