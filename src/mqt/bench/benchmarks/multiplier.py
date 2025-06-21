# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Multiplier."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import MultiplierGate

from ._registry import register_benchmark


@register_benchmark("multiplier", description="Multiplier")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a multiplier circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit, must be divisible by 4.

    Returns:
           QuantumCircuit: The constructed multiplier circuit.

    See Also:
        :class:`qiskit.circuit.library.MultiplierGate`
    """
    if num_qubits % 4 or num_qubits < 4:
        msg = "num_qubits must be an integer ≥ 4 and divisible by 4."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 2 - 1
    gate = MultiplierGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    qc.measure_all()
    qc.name = "multiplier"

    return qc
