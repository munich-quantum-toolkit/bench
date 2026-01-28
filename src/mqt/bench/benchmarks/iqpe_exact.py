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
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister, IfElseOp

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
    if num_qubits < 2:
<<<<<<< HEAD
        raise ValueError("num_qubits must be >= 2 (1 ancilla + at least 1 phase bit)")
    num_bits = num_qubits - 1  # because of ancilla qubit
    q = QuantumRegister(num_qubits, "q")
    c = ClassicalRegister(num_bits, "c")
    qc = QuantumCircuit(q, c, name="iqpeexact")
=======
        msg = "num_qubits must be >= 2 (1 ancilla + at least 1 phase bit)"
        raise ValueError(msg)
    num_qubits = num_qubits - 1  # because of ancilla qubit
    q0 = QuantumRegister(1, "q0")
    q1 = QuantumRegister(num_qubits, "q1")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q0, q1, c, name="iqpeexact")
>>>>>>> 27061228820a714057682df966e1cbb469f36e32

    # Generate a random n-bit integer as a target phase "theta". The phase can be exactly
    # estimated
    rng = random.Random(10)
    theta = 0
    while theta == 0:
        theta = rng.getrandbits(num_bits)
    lam = Fraction(0, 1)
    for i in range(num_bits):
        if theta & (1 << (num_bits - i - 1)):
            lam += Fraction(1, (1 << i))

    # We apply an X gate to the q[1] qubit, to prepare the target qubit in the
    # |1> state
    qc.x(q[0])

    for k in range(num_bits):
        index = num_bits - 1 - k
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
            m_index = num_bits - 1 - i
            true_angle = -1.0 / (1 << (k - i))

            with qc.if_test((c[m_index], 1)):
                qc.p(true_angle * np.pi, q[0])

        qc.h(q[0])
        # We measure and store the result for future corrections
        qc.measure(q[0], c[index])

    return qc
