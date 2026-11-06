# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""HHL benchmark for a fixed two-dimensional linear system."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate, UGate

from ._registry import register_benchmark


@register_benchmark("hhl", description="Harrow-Hassidim-Lloyd Algorithm (HHL)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    r"""Solve a fixed two-dimensional linear system using HHL.

    .. math::

        A x = |1\rangle, \qquad
        A = \begin{pmatrix} 1 & 1 \\ 1 & 3 \end{pmatrix}.

    The eigenvalues are :math:`2 \pm \sqrt{2}`. Shifted and scaled evolution
    maps their phases to zero and one half, so phase estimation is exact with
    any supported register width. The reciprocal rotation uses the original
    eigenvalues, with scale :math:`2 - \sqrt{2}`.

    Condition the system result in ``c`` on ``success[0] == 1``. The successful
    system state is :math:`(-|0\rangle + |1\rangle)/\sqrt{2}`.

    Args:
        num_qubits: Total width: one system qubit, ``num_qubits - 2`` phase
            qubits, and one success ancilla. Must be at least 3.

    Returns:
        The HHL circuit, including success and system measurements.
    """
    if num_qubits < 3:
        msg = "Number of qubits must be at least 3 for HHL."
        raise ValueError(msg)

    system = QuantumRegister(1, "sys")
    phase = QuantumRegister(num_qubits - 2, "phase")
    ancilla = QuantumRegister(1, "ancilla")
    result = ClassicalRegister(1, "c")
    success = ClassicalRegister(1, "success")
    qc = QuantumCircuit(system, phase, ancilla, result, success, name="hhl")
    qc.x(system[0])

    # U = exp(i*pi*(A - lambda_min*I)/(lambda_max - lambda_min)). Its square is I.
    evolution = UGate(np.pi / 2, np.pi, 0)
    estimation = QuantumCircuit(len(phase) + 1)
    estimation.h(range(len(phase)))
    estimation.append(evolution.control(), [0, len(phase)])
    estimation.append(QFTGate(len(phase)).inverse(), range(len(phase)))
    estimation_qubits = [*phase, *system]
    qc.compose(estimation, estimation_qubits, inplace=True)

    qc.ry(np.pi, ancilla[0])
    ratio = (2 - np.sqrt(2)) / (2 + np.sqrt(2))
    qc.cry(2 * np.arcsin(ratio) - np.pi, phase[-1], ancilla[0])
    qc.compose(estimation.inverse(), estimation_qubits, inplace=True)
    qc.measure(system, result)
    qc.measure(ancilla, success)
    return qc
