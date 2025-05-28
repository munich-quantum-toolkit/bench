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

import numpy as np
from qiskit.circuit import QuantumCircuit


def create_circuit(num_qubits: int, depth: int = 2) -> QuantumCircuit:
    """Returns a Qiskit circuit based on the copula circuit architecture from the QUARK framework.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        depth: depth of the returned quantum circuit
    """
    rng = np.random.default_rng(10)

    n_registers = 2
    n = num_qubits // n_registers

    qc = QuantumCircuit(num_qubits)

    for k in range(n):
        qc.h(k)

    for j in range(n_registers - 1):
        for k in range(n):
            qc.cx(k, k + n * (j + 1))

    qc.barrier()

    shift = 0
    for _ in range(depth):
        for k in range(n):
            for j in range(n_registers):
                qubit_index = j * n + k
                qc.rz(rng.random() * 2 * np.pi, qubit_index)
                qc.rx(rng.random() * 2 * np.pi, qubit_index)
                qc.rz(rng.random() * 2 * np.pi, qubit_index)

        k = 3 * n + shift
        for i in range(n):
            for j in range(i + 1, n):
                for layer in range(n_registers):
                    qc.rxx(rng.random() * 2 * np.pi, layer * n + i, layer * n + j)

            k += 1
        shift += 3 * n + comb(n, 2)

    qc.measure_all()
    qc.name = "quarkcopula"

    return qc
