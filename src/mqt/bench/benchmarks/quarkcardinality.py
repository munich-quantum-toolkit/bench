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
