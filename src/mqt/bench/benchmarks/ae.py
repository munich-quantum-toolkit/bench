# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Amplitude estimation benchmark definition. Code is based on https://qiskit.org/documentation/finance/tutorials/00_amplitude_estimation.html."""

from __future__ import annotations

from math import asin, sqrt

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import PermutationGate, RYGate, phase_estimation

from ._registry import register_benchmark


@register_benchmark("ae", description="Amplitude Estimation")
def create_circuit(num_qubits: int, probability: float = 0.2) -> QuantumCircuit:
    """Build a circuit for amplitude estimation.

    Args:
        num_qubits: Total width, including one target qubit and at least one evaluation qubit.
        probability: Probability of the good state, from 0 to 1 inclusive.

    Returns:
        A circuit that measures the evaluation register followed by the target qubit.
        Evaluation qubit 0 is the most significant phase bit.
    """
    if num_qubits < 2:
        msg = "Number of qubits must be at least 2 (1 evaluation + 1 target)."
        raise ValueError(msg)

    if not 0 <= probability <= 1:
        msg = "probability must be between 0 and 1."
        raise ValueError(msg)

    theta_p = 2 * asin(sqrt(probability))
    num_eval_qubits = num_qubits - 1
    pe = phase_estimation(num_eval_qubits, RYGate(2 * theta_p))
    qc = QuantumCircuit(*pe.qregs, name="ae")
    qc.ry(theta_p, num_eval_qubits)
    # Express the final bit reversal as swaps for OpenQASM export.
    qc.compose(pe.decompose(gates_to_decompose=PermutationGate), inplace=True)
    qc.measure_all()
    return qc
