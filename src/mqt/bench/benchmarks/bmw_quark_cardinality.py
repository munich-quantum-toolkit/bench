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

"""Cardinality circuit from the generative modeling application in QUARK framework. https://github.com/QUARK-framework/QUARK."""

from __future__ import annotations

from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit
from qiskit.circuit.library import RXXGate

from ._registry import register_benchmark


@register_benchmark("bmw_quark_cardinality", description="Cardinality Circuit (QUARK)")
def create_circuit(num_qubits: int, depth: int = 3) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the cardinality circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
    """
    qc = QuantumCircuit(num_qubits)

    # === Precompute parameter count ===
    num_initial = 2 * num_qubits
    num_rxx = depth * (num_qubits - 1)
    num_mid_layers = (depth - 2) * 2 * num_qubits if depth > 1 else 0
    num_final_layer = 3 * num_qubits if depth >= 2 else 0
    total_params = num_initial + num_rxx + num_mid_layers + num_final_layer

    param_vector = ParameterVector("p", length=total_params)

    param_index = 0

    def get_param() -> Parameter:
        nonlocal param_index
        param = param_vector[param_index]
        param_index += 1
        return param

    # === Initial single-qubit rotations ===
    for q in range(num_qubits):
        qc.rx(get_param(), q)
        qc.rz(get_param(), q)

    # === Layered structure ===
    for d in range(depth):
        qc.barrier()
        for q in range(num_qubits - 1):
            qc.append(RXXGate(get_param()), [q, q + 1])
        qc.barrier()

        if d == depth - 2:
            for q in range(num_qubits):
                qc.rx(get_param(), q)
                qc.rz(get_param(), q)
                qc.rx(get_param(), q)
        elif d < depth - 2:
            for q in range(num_qubits):
                qc.rx(get_param(), q)
                qc.rz(get_param(), q)

    qc.measure_all()
    qc.name = "bmw_quark_cardinality"

    return qc
