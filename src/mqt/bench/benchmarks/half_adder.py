# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Half Adder."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import HalfAdderGate

from ._registry import register_benchmark


@register_benchmark("half_adder", description="Half Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a half adder circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit, must be odd and bigger than 3
                so that there is a carry-out bit and the rest can be divided by 2 for both registers.

    Returns:
           QuantumCircuit: The constructed half adder circuit.

    See Also:
        :class:`qiskit.circuit.library.HalfAdderGate`
    """
    # Expect one extra qubit for the carry-out bit → total must be odd ≥ 3
    if num_qubits % 2 == 0 or num_qubits < 3:
        msg = "num_qubits must be an odd integer ≥ 3."
        raise ValueError(msg)

    num_state_qubits = (num_qubits - 1) // 2
    gate = HalfAdderGate(num_state_qubits)

    qc = QuantumCircuit(gate.num_qubits)
    qc.append(gate, qc.qubits)
    qc.measure_all()
    qc.name = "half_adder"

    return qc
