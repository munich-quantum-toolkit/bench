# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Copula circuit from the generative modeling application in QUARK framework. https://github.com/QUARK-framework/QUARK."""

from __future__ import annotations

from math import comb

import numpy as np
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit


def create_circuit(num_qubits: int, depth: int = 2, random_parameters: bool = True) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the copula circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
        random_parameters: If True, assign random parameter values; if False, use symbolic parameters.
    """
    assert num_qubits % 2 == 0, "Number of qubits must be divisible by 2."

    n_registers = 2
    n = num_qubits // n_registers
    rng = np.random.default_rng(10)
    qc = QuantumCircuit(num_qubits)

    # === Compute number of parameters ===
    num_single_qubit_gates = depth * n_registers * n * 3
    num_rxx_gates = depth * n_registers * comb(n, 2)
    total_params = num_single_qubit_gates + num_rxx_gates

    param_vector: ParameterVector | None = None
    if not random_parameters:
        param_vector = ParameterVector("p", total_params)

    param_index = 0

    def get_param() -> float | Parameter:
        nonlocal param_index
        if random_parameters:
            return rng.random() * 2 * np.pi
        assert param_vector is not None
        value = param_vector[param_index]
        param_index += 1
        return value

    # === Initial Hadamards on first register ===
    for q in range(n):
        qc.h(q)

    # === CNOTs to entangle registers ===
    for q in range(n):
        qc.cx(q, q + n)

    qc.barrier()

    # === Layered RZ-RX-RZ and RXX ===
    for _ in range(depth):
        # Apply RZ-RX-RZ to each qubit
        for q in range(num_qubits):
            qc.rz(get_param(), q)
            qc.rx(get_param(), q)
            qc.rz(get_param(), q)

        # Intra-register RXX (full connectivity)
        for reg in range(n_registers):
            base = reg * n
            for i in range(n):
                for j in range(i + 1, n):
                    qc.rxx(get_param(), base + i, base + j)

        qc.barrier()

    qc.measure_all()
    qc.name = "quarkcopula"

    return qc
