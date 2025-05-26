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
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.library import RXXGate


def create_circuit(num_qubits: int, depth: int = 3, random_parameters: bool = True) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the cardinality circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
        random_parameters: If True, assign random parameter values; if False, use symbolic parameters.
    """
    qc = QuantumCircuit(num_qubits)
    rng = np.random.default_rng(10)

    # === Parameter allocation ===
    parameters = []
    param_counter = 0

    def get_param(name: str) -> Parameter | float:
        nonlocal param_counter
        if random_parameters:
            return rng.random() * 2 * np.pi
        p = Parameter(f"{name}_{param_counter}")
        parameters.append(p)
        param_counter += 1
        return p

    # === Initial single-qubit rotations ===
    for q in range(num_qubits):
        qc.rx(get_param("rx_init"), q)
        qc.rz(get_param("rz_init"), q)

    # === Layered structure ===
    for d in range(depth):
        qc.barrier()
        # RXX entangling layer
        for q in range(num_qubits - 1):
            qc.append(RXXGate(get_param(f"rxx_d{d}")), [q, q + 1])
        qc.barrier()

        # Mid or final layer single-qubit rotations
        for q in range(num_qubits):
            qc.rx(get_param(f"rx1_d{d}"), q)
            if d == depth - 2:
                qc.rz(get_param(f"rz_d{d}"), q)
                qc.rx(get_param(f"rx2_d{d}"), q)
            elif d < depth - 2:
                qc.rz(get_param(f"rz_d{d}"), q)

    qc.measure_all()
    qc.name = "quarkcardinality"

    return qc
