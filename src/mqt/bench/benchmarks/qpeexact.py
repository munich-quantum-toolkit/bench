# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""QPE exact benchmark definition."""

from __future__ import annotations

import random
from fractions import Fraction

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.synthesis import synth_qft_full

from ._registry import register_benchmark


@register_benchmark("qpeexact", description="Quantum Phase Estimation (QPE) exactly representable phase")
def create_circuit(num_qubits: int, seed: int | None = 10) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Quantum Phase Estimation algorithm for a phase which can be exactly estimated.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be at least 2.
        seed: Random seed for the target phase.

    Returns:
        QuantumCircuit: A quantum circuit implementing the Quantum Phase Estimation algorithm for a phase which can be exactly estimated.
    """
    if num_qubits <= 1:
        msg = "Number of qubits must be at least 2 for QPE exact."
        raise ValueError(msg)

    num_qubits = num_qubits - 1  # because of ancilla qubit
    q = QuantumRegister(num_qubits, "q")
    psi = QuantumRegister(1, "psi")
    c = ClassicalRegister(num_qubits, "c")
    qc = QuantumCircuit(q, psi, c, name="qpeexact")

    # get random n-bit string as target phase
    rng = random.Random(seed)
    theta = 0
    while theta == 0:
        theta = rng.getrandbits(num_qubits)
    lam = Fraction(0, 1)
    for i in range(num_qubits):
        if theta & (1 << (num_qubits - i - 1)):
            lam += Fraction(1, (1 << i))

    qc.x(psi)
    qc.h(q)

    for i in range(num_qubits):
        angle = (lam * (1 << i)) % 2
        if angle > 1:
            angle -= 2
        if angle != 0:
            qc.cp(angle * np.pi, psi, q[i])

    qc.compose(
        synth_qft_full(num_qubits=num_qubits, inverse=True),
        inplace=True,
        qubits=list(range(num_qubits)),
    )
    qc.barrier()
    qc.measure(q, c)

    return qc
