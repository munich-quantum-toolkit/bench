# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Cardinality circuit from the generative modeling application in QUARK framework. https://github.com/QUARK-framework/QUARK."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import RXXGate


def create_circuit(num_qubits: int, depth: int = 3) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the cardinality circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
    """
    rng = np.random.default_rng(10)
    qc = QuantumCircuit(num_qubits)

    for k in range(num_qubits):
        qc.rx(rng.random() * 2 * np.pi, k)
        qc.rz(rng.random() * 2 * np.pi, k)

    for d in range(depth):
        qc.barrier()
        for k in range(num_qubits - 1):
            qc.append(RXXGate(rng.random() * 2 * np.pi), [k, k + 1])

        qc.barrier()

        if d == depth - 2:
            for k in range(num_qubits):
                qc.rx(rng.random() * 2 * np.pi, k)
                qc.rz(rng.random() * 2 * np.pi, k)
                qc.rx(rng.random() * 2 * np.pi, k)
        elif d < depth - 2:
            for k in range(num_qubits):
                qc.rx(rng.random() * 2 * np.pi, k)
                qc.rz(rng.random() * 2 * np.pi, k)

    qc.measure_all()
    qc.name = "quarkcardinality"

    return qc
