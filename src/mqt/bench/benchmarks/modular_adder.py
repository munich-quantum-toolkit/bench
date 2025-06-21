# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Modular Adder."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import ModularAdderGate

from ._registry import register_benchmark


@register_benchmark("modular_adder", description="Modular Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a modular adder circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit, must be even and bigger than 2
                so that they can be divided by 2 for both registers.

    Returns:
           QuantumCircuit: The constructed full adder circuit.

    See Also:
        :class:`qiskit.circuit.library.ModularAdderGate`
    """
    # Same number of quibts for both registers  → total must be even ≥ 2
    if num_qubits % 2 or num_qubits < 2:
        msg = "num_qubits must be an even integer ≥ 2."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 2
    gate = ModularAdderGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    qc.measure_all()
    qc.name = "modular_adder"

    return qc
