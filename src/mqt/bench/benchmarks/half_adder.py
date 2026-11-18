# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Half Adder."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit
from qiskit.circuit.library import HalfAdderGate

from ._registry import register_benchmark


@register_benchmark("half_adder", description="Half Adder")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Build a half adder with carry-out.

    Args:
        num_qubits: Total width of two equal operands and the carry-out qubit.
            Must be odd and at least 3.

    Returns:
        A circuit that measures only the sum into ``result``, least-significant bit first.
        The highest result bit is the carry-out.

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
    result = ClassicalRegister(num_state_qubits + 1, "result")
    qc.add_register(result)
    qc.barrier()
    qc.measure(qc.qubits[num_state_qubits:], result)
    qc.name = "half_adder"

    return qc
