# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dynamic GHZ benchmark definition."""



from __future__ import annotations

from qiskit.circuit import QuantumCircuit, QuantumRegister, ClassicalRegister

from qiskit.circuit.classical import expr

from ._registry import register_benchmark

@register_benchmark("ghz_dynamic", description="Dynamic GHZ State")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a dynamic quantum circuit implementing the GHZ state.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_qubits//2, 'mid_measurement')
    qc = QuantumCircuit(q, c, name="ghz_dynamic")

    # Apply Haddamard gates to all even qubits
    for i in range(0, num_qubits, 2):
        qc.h(i)


    # Apply CNOT gates from all even qubits to the previous and next one, if total number of qubits is even we ignore the last CNOT
    for i in range(0, num_qubits, 2):
        j = i-1
        z = i+1
        if j >= 0:
            qc.cx(i,j)
        if z < num_qubits-1:
            qc.cx(i,z)

    j = 0

    # Intermediate measurements on the odd qubits, the if_test statement is there to simulate a reset operation as this is not accepted by some hardware
    for i in range(1, num_qubits, 2):
        qc.measure(i,j)
        j+=1
        with qc.if_test((c[0],1)):
            qc.x(i)

    j = 0
    if num_qubits>1:
        condition = c[0]

    # We apply a X gate to all even qubits other than the first one if the exor of the intermediate measurements of all the previous qubits is 1
    for i in range(2, num_qubits, 2):
        with qc.if_test(expr.equal(condition, True)):
                qc.x(i)
        j+=1
        if j<num_qubits//2:
            condition =  expr.bit_xor(condition, c[j])
    
    # We apply CNOT gates to the qubits we measured before and reseted from the previous qubit
    for i in range(0, num_qubits-1, 2):
        j = i+1
        qc.cx(i,j)

    qc.measure_all()
    return qc


