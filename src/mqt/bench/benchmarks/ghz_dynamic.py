# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dynamic GHZ benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.classical import expr

from ._registry import register_benchmark


@register_benchmark("ghz_dynamic", description="Dynamic GHZ State")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Prepare a GHZ state using intermediate measurements and classical feedback.

    See Fig. 5 of https://arxiv.org/abs/2308.13065 for the dynamic construction.

    Args:
        num_qubits: Number of qubits in the state. Must be at least 1.

    Returns:
        A circuit with the final readout in ``final_measurement``. For widths above one,
        ``mid_measurement`` holds the intermediate outcomes.
    """
    q = QuantumRegister(num_qubits, "q")
    final_measure = ClassicalRegister(num_qubits, "final_measurement")
    qc = QuantumCircuit(q, final_measure, name="ghz_dynamic")

    # If num_qubits = 1, then we just apply a Hadamard gate to the qubit
    if num_qubits == 1:
        qc.h(0)
        qc.measure(q, final_measure)
        return qc

    mid_measure = ClassicalRegister(num_qubits // 2, "mid_measurement")
    qc.add_register(mid_measure)

    # Apply Hadamard gates to all even qubits
    qc.h(range(0, num_qubits, 2))

    # Apply CNOT gates from all even qubits to the previous and next one.
    # If the total number of qubits is even, ignore the last CNOT.
    for i in range(0, num_qubits, 2):
        previous_qubit = i - 1
        next_qubit = i + 1
        if previous_qubit >= 0:
            qc.cx(i, previous_qubit)
        if next_qubit < num_qubits - 1:
            qc.cx(i, next_qubit)

    # Measure the odd qubits and reset them conditionally, since some hardware does not support reset operations.
    for classical_bit, qubit in zip(mid_measure, range(1, num_qubits, 2), strict=True):
        qc.measure(qubit, classical_bit)
        with qc.if_test((classical_bit, 1)):
            qc.x(qubit)

    condition = mid_measure[0]

    # Apply X to each even qubit after the first when the XOR of all preceding intermediate measurements is 1.
    for i in range(2, num_qubits, 2):
        with qc.if_test(expr.equal(condition, True)):
            qc.x(i)
        if i // 2 < len(mid_measure):
            condition = expr.bit_xor(condition, mid_measure[i // 2])

    # We apply CNOT gates to the qubits we measured before and reset from the previous qubit
    for i in range(0, num_qubits - 1, 2):
        qc.cx(i, i + 1)

    qc.measure(q, final_measure)
    return qc
