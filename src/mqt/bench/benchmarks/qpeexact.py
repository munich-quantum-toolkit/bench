# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""QOE exact benchmark definition."""

from __future__ import annotations

import random
from fractions import Fraction

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.synthesis import synth_qft_full

from ._reference import MetricApplicability, ObjectiveSpec, ReferenceSpec, SparseReference
from ._registry import register_benchmark, register_reference


@register_benchmark("qpeexact", description="Quantum Phase Estimation (QPE) exactly representable phase")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Quantum Phase Estimation algorithm for a phase which can be exactly estimated.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be at least 2.

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
    random.seed(10)
    theta = 0
    while theta == 0:
        theta = random.getrandbits(num_qubits)
    lam = Fraction(0, 1)
    # print("theta : ", theta, "correspond to", theta / (1 << n), "bin: ")
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


@register_reference("qpeexact")
def create_reference(num_qubits: int) -> ReferenceSpec:
    """Reference spec for the QPE-exact circuit.

    The circuit estimates a phase that is exactly representable with
    ``num_qubits - 1`` estimation bits, so the measurement is deterministic:
    a single bitstring is observed with probability 1.

    The target phase ``theta`` is derived from the same fixed seed
    (``random.seed(10)``) used in :func:`create_circuit`, so we can
    reproduce it here without running the circuit.

    In Qiskit's QPE layout the estimation register ``q[0..n-1]`` is
    measured into classical register ``c[0..n-1]``.  The output string
    is the binary representation of ``theta`` with ``n`` bits, MSB first
    (big-endian over classical bits) — i.e. ``format(theta, '0{n}b')``.

    Arguments:
        num_qubits: total qubits including the eigenstate qubit
            (same as passed to :func:`create_circuit`).
    """
    if num_qubits <= 1:
        msg = "Number of qubits must be at least 2 for QPE exact."
        raise ValueError(msg)

    n = num_qubits - 1  # estimation qubits (mirrors create_circuit's first line)

    # Reproduce the same seed-derived theta used in create_circuit
    random.seed(10)
    theta = 0
    while theta == 0:
        theta = random.getrandbits(n)

    # Derive the phase fraction lambda (same computation as create_circuit)
    lam = Fraction(0, 1)
    for i in range(n):
        if theta & (1 << (n - i - 1)):
            lam += Fraction(1, (1 << i))
    phase = float(lam)

    # The measurement collapses to the binary representation of theta with n digits.
    # Qiskit classical string is big-endian: c[n-1] (MSB) ... c[0] (LSB).
    # c[i] = bit i of theta counted from LSB, so string = format(theta, '0nb') directly.
    qiskit_string = format(theta, f"0{n}b")

    return ReferenceSpec(
        circuit="qpeexact",
        n_qubits=num_qubits,
        measured_qubits=list(range(n)),
        bit_order="qiskit-little-endian",
        reference=SparseReference(entries={qiskit_string: 1.0}),
        objective=ObjectiveSpec(type="phase", value=phase),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True, ideal=1.0),
            "tvd": MetricApplicability(applicable=True, ideal=0.0),
            "success_probability": MetricApplicability(applicable=True, ideal=1.0),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
