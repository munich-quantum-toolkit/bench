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

    rng = np.random.default_rng(10)
    n_registers = 2
    n = num_qubits // n_registers
    qc = QuantumCircuit(num_qubits)

    # === Total number of parameters ===
    num_rzrxrz = depth * n_registers * n * 3  # 3 rotations per qubit per layer
    num_rxx = depth * n_registers * comb(n, 2)  # full intra-register RXX
    total_params = num_rzrxrz + num_rxx

    param_vector: ParameterVector | None = None
    if not random_parameters:
        param_vector = ParameterVector("p", length=total_params)

    param_index = 0

    def get_param() -> float | Parameter:
        nonlocal param_index
        if random_parameters:
            return rng.random() * 2 * np.pi
        assert param_vector is not None
        param = param_vector[param_index]
        param_index += 1
        return param

    # === Initial Hadamards on first register ===
    for k in range(n):
        qc.h(k)

    # CNOTs from register 0 to 1
    for j in range(n_registers - 1):
        for k in range(n):
            qc.cx(k, k + n * (j + 1))

    qc.barrier()

    shift = 0
    for _d in range(depth):
        # RZ - RX - RZ for each qubit
        for k in range(n):
            for j in range(n_registers):
                qubit_index = j * n + k
                qc.rz(get_param(), qubit_index)
                qc.rx(get_param(), qubit_index)
                qc.rz(get_param(), qubit_index)

        # Intra-register RXX
        k = 3 * n + shift
        for i in range(n):
            for j in range(i + 1, n):
                for layer in range(n_registers):
                    q0 = layer * n + i
                    q1 = layer * n + j
                    qc.rxx(get_param(), q0, q1)

        shift += 3 * n + comb(n, 2)
        qc.barrier()

    qc.measure_all()
    qc.name = "quarkcopula"

    return qc
