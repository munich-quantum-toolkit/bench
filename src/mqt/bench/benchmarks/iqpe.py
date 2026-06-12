# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""IQPE benchmark definition."""

from __future__ import annotations

import random
from fractions import Fraction

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("iqpe", description="Iterative Quantum Phase Estimation (IQPE)")
def create_circuit(
    num_qubits: int, exact: bool = True, rotation_threshold: float = 1e-15, seed: int = 10
) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Iterative Quantum Phase Estimation algorithm.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be at least 2.
        exact: Whether to use the exact version of the algorithm.
        rotation_threshold: Threshold for adding rotation gates in the feedback step. Rotation gates with smaller angles will be omitted to reduce circuit complexity.
        seed: Seed for the random number generator.

    Returns:
        QuantumCircuit: A quantum circuit implementing the Iterative Quantum Phase Estimation algorithm.
    """
    if num_qubits <= 1:
        msg = "Number of qubits must be at least 2 for IQPE."
        raise ValueError(msg)

    num_iterations = num_qubits - 1  # one ancilla qubit, rest for iterations
    ancilla = QuantumRegister(1, "q")
    psi = QuantumRegister(1, "psi")
    c = ClassicalRegister(num_iterations, "c")
    qc = QuantumCircuit(ancilla, psi, c, name="iqpe")

    # get random n-bit string as target phase
    theta = 0
    random.seed(seed)
    if exact:
        while theta == 0:
            theta = random.getrandbits(num_iterations)
        lam = Fraction(theta, 1 << num_iterations)  # phase to be estimated

    elif not exact:
        while theta == 0 or (theta & 1) == 0:  # Ensure an odd theta so phase cannot be exactly represented with n bits
            theta = random.getrandbits(num_iterations)
        lam = Fraction(theta, 1 << (num_iterations + 1))  # phase to be estimated, with extra bit

    qc.x(psi)  # prepare |1> state

    for i in range(num_iterations, 0, -1):  # start from n
        qc.h(ancilla[0])  # put ancilla in superposition

        frac = (lam * (1 << (i - 1))) % 1  # exact Fraction in [0, 1)
        angle = 2 * np.pi * frac  # in [0, 2*pi)
        if angle > np.pi:
            angle -= 2 * np.pi  # shift into (-pi, pi]
        qc.cp(angle, psi, ancilla[0])

        for meas_idx in range(i, num_iterations):  # bits already measured this run
            with qc.if_test((c[meas_idx], 1)):
                exponent = meas_idx - (i - 1) + 1
                rotation_angle = -2 * np.pi * Fraction(1, 1 << exponent)
                if abs(rotation_angle) > rotation_threshold:  # avoid adding negligible gates
                    qc.rz(rotation_angle, ancilla[0])

        qc.h(ancilla[0])
        qc.measure(ancilla[0], c[i - 1])
        with qc.if_test((c[i - 1], 1)):
            qc.x(ancilla[0])  # reset ancilla for next iteration

    return qc
