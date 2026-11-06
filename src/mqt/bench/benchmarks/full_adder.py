# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Full Adder."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit
from qiskit.circuit.library import FullAdderGate

from ._registry import register_benchmark


@register_benchmark("full_adder", description="Full Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Build a full adder with carry-in and carry-out.

    Args:
        num_qubits: Total width of two equal operands and two carry qubits.
            Must be even and at least 4.

    Returns:
        A circuit that measures only the sum into ``result``, least-significant bit first.
        The highest result bit is the carry-out.

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
    result = ClassicalRegister(num_state_qubits + 1, "result")
    qc.add_register(result)
    qc.barrier()
    qc.measure(qc.qubits[num_state_qubits + 1 :], result)
    qc.name = "full_adder"

    return qc
