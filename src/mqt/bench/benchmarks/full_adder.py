# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Full Adder."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import FullAdderGate

from ._registry import register_benchmark


@register_benchmark("full_adder", description="Full Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a full adder circuit.

    Arguments:
            num_qubits: number of qubits of the returned quantum circuit, must be even and bigger than 4
                so that there is a carry-in bit, carry-out bit, and the rest can be divided by 2 for both registers.

    Returns:
           QuantumCircuit: The constructed full adder circuit.

    See Also:
        :class:`qiskit.circuit.library.FullAdderGate`
    """
    # Expect two extra qubit for the carry-in and carry-out bits → total must be even ≥ 4
    if num_qubits % 2 or num_qubits < 4:
        msg = "num_qubits must be an even integer ≥ 4."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 2 - 1
    gate = FullAdderGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    qc.measure_all()
    qc.name = "full_adder"

    return qc
