# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

#  Copyright 2021 The QUARK Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Copula circuit from the generative modeling application in QUARK framework. https://github.com/QUARK-framework/QUARK."""

from __future__ import annotations

from math import comb

from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit

from ._registry import register_benchmark


@register_benchmark("bmw_quark_copula", description="Copula Circuit (QUARK)")
def create_circuit(num_qubits: int, depth: int = 2) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the copula circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
    """
    assert num_qubits % 2 == 0, "Number of qubits must be divisible by 2."

    n_registers = 2
    n = num_qubits // n_registers
    qc = QuantumCircuit(num_qubits)

    # === Compute number of parameters ===
    num_single_qubit_gates = depth * n_registers * n * 3
    num_rxx_gates = depth * n_registers * comb(n, 2)
    total_params = num_single_qubit_gates + num_rxx_gates

    param_vector = ParameterVector("p", total_params)

    param_index = 0

    def get_param() -> Parameter:
        nonlocal param_index
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
    qc.name = "bmw_quark_copula"

    return qc
