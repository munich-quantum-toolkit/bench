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
    """Returns a quantum circuit implementing the dynamic Quantum Fourier Transform.

    The circuit implements the semiclassical QFT followed by measurement from Griffiths and Niu
    and the dynamic QFT construction described in Phys. Rev. Lett. 133, 150602 (2024). It mirrors
    the operation order of the regular QFT benchmark, but replaces controlled phase gates from
    already measured qubits by classically controlled phase rotations.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit.

    Returns:
        QuantumCircuit: a quantum circuit implementing the dynamic Quantum Fourier Transform.
    """
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="dynamic_qft")

    for qubit in reversed(range(num_qubits)):
        measured_bit = num_qubits - qubit - 1

        for control_qubit in range(num_qubits - 1, qubit, -1):
            control_bit = num_qubits - control_qubit - 1
            with qc.if_test((c[control_bit], 1)):
                qc.p(math.pi / (1 << (control_qubit - qubit)), q[qubit])

        qc.h(q[qubit])
        qc.measure(q[qubit], c[measured_bit])

    return qc
