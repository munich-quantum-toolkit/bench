# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Copula circuit from the generative modeling application in QUARK framework. https://github.com/QUARK-framework/QUARK."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import Parameter, QuantumCircuit


def create_circuit(num_qubits: int, depth: int = 2, random_parameters: bool = True) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the copula circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
        random_parameters: If True, assign random parameter values; if False, use symbolic parameters.
    """
    assert num_qubits % 2 == 0, "Number of qubits must be divisible by number of registers (2)."

    rng = np.random.default_rng(10)
    n_registers = 2
    n = num_qubits // n_registers
    qc = QuantumCircuit(num_qubits)

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

    # Initial layer of Hadamard gates
    for k in range(n):
        qc.h(k)

    # Entanglement between registers using CNOTs
    for j in range(n_registers - 1):
        for k in range(n):
            qc.cx(k, k + n * (j + 1))

    qc.barrier()

    # Repeated parameterized layers
    for d in range(depth):
        # Single-qubit rotations: RZ - RX - RZ
        for k in range(n):
            for j in range(n_registers):
                qubit_index = j * n + k
                qc.rz(get_param(f"rz1_d{d}_q{qubit_index}"), qubit_index)
                qc.rx(get_param(f"rx_d{d}_q{qubit_index}"), qubit_index)
                qc.rz(get_param(f"rz2_d{d}_q{qubit_index}"), qubit_index)

        # Intra-register RXX entangling gates
        for i in range(n):
            for j in range(i + 1, n):
                for r in range(n_registers):
                    q0 = r * n + i
                    q1 = r * n + j
                    theta = get_param(f"rxx_d{d}_r{r}_q{q0}_{q1}")
                    qc.rxx(theta, q0, q1)

        qc.barrier()

    qc.measure_all()
    qc.name = "quarkcopula"

    return qc
