# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Iterative Quantum Phase Estimation (IQPE)."""

from __future__ import annotations

import random
from fractions import Fraction

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from ._registry import register_benchmark


@register_benchmark("iqpeexact", description="Iterative Quantum Phase Estimation (IQPE)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a dynamic quantum circuit implementing the Iterative Quantum Phase Estimation algorithm.

    Arguments:
        num_qubits: total number of qubits.

    Returns:
        QuantumCircuit: a dynamic quantum circuit implementing the Iterative Quantum Phase Estimation algorithm for a phase which can be exactly estimated

    """
    # We just use 2 quantum registers: q[1] is the main register where
    # the eigenstate will be encoded, q[0] is the ancillary qubit where the phase
    # will be encoded. Only the ancillary qubit is measured, and the result will
    # be stored in "c", the classical register.
    num_qubits = num_qubits - 1  # because of ancilla qubit
    q = QuantumRegister(2, "q")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, c, name="iqpeexact")

    # Generate a random n-bit integer as a target phase "theta". The phase can be exactly
    # estimated
    random.seed(10)
    theta = 0
    while theta == 0:
        theta = random.getrandbits(num_qubits)
    lam = Fraction(0, 1)
    for i in range(num_qubits):
        if theta & (1 << (num_qubits - i - 1)):
            lam += Fraction(1, (1 << i))

    # print(f"Debug: theta = {theta}, lam = {float(lam)}")

    # We apply an X gate to the q[1] qubit, to prepare the target qubit in the
    # |1> state
    qc.x(q[1])

    for k in range(num_qubits):
        index = num_qubits - 1 - k
        # We reset the ancillary qubit in order to reuse in each iteration
        qc.reset(q[0])
        qc.h(q[0])

        # Controlled unitary. The angle is normalized from
        # [0, 2] to [-1, 1], which minimize the errors because uses shortest rotations
        angle = float((lam * (1 << index)) % 2)
        if angle > 1:
            angle -= 2

        # We use pi convention for simplicity
        qc.cp(angle * np.pi, q[0], q[1])

        # We apply phase corrections based on previous measurements.
        for i in range(k):
            m_index = num_qubits - 1 - i
            true_angle = -1.0 / (1 << (k - i))

            with qc.if_test((c[m_index], 1)):
                qc.p(true_angle * np.pi, q[0])

        qc.h(q[0])
        # We measure and store the result for future corrections
        qc.measure(q[0], c[k])

    return qc
