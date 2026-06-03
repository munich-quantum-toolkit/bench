# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Iterative Quantum Phase Estimation benchmark definition."""

from __future__ import annotations

import math

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("iqpe", description="Iterative Quantum Phase Estimation (IQPE)")
def create_circuit(num_qubits: int, num_bits: int = 3, phase: float = 0.625) -> QuantumCircuit:
    """Returns a dynamic circuit implementing Iterative Quantum Phase Estimation.

    Arguments:
        num_qubits: Number of qubits of the returned quantum circuit. Must be at least 2.
        num_bits: Number of measured phase bits.
        phase: Target phase as a fraction of one full turn. Must be in ``[0, 1)``.

    Returns:
        QuantumCircuit: The constructed IQPE circuit.
    """
    if num_qubits < 2:
        msg = "Number of qubits must be at least 2 for IQPE."
        raise ValueError(msg)
    if num_bits < 1:
        msg = "num_bits must be at least 1 for IQPE."
        raise ValueError(msg)
    if not 0 <= phase < 1:
        msg = "phase must be in the interval [0, 1)."
        raise ValueError(msg)

    measurement = QuantumRegister(1, "measurement")
    target = QuantumRegister(num_qubits - 1, "target")
    phase_bits = ClassicalRegister(num_bits, "phase")
    qc = QuantumCircuit(measurement, target, phase_bits, name="iqpe")

    phase_per_target = phase / len(target)
    for target_qubit in target:
        qc.x(target_qubit)

    for bit in reversed(range(num_bits)):
        qc.h(measurement[0])

        # Split the phase over the target register so |1...1> has the requested eigenphase.
        for target_qubit in target:
            qc.cp(2 * math.pi * phase_per_target * (2**bit), measurement[0], target_qubit)

        for correction_bit in range(bit + 1, num_bits):
            with qc.if_test((phase_bits[correction_bit], 1)):
                qc.rz(-math.pi / (2 ** (correction_bit - bit)), measurement[0])

        qc.h(measurement[0])
        qc.measure(measurement[0], phase_bits[bit])
        with qc.if_test((phase_bits[bit], 1)):
            qc.x(measurement[0])

    return qc
