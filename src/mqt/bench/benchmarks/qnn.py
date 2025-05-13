# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Quantum Neural Network benchmark definition. Code is inspired by https://qiskit.org/ecosystem/machine-learning/stubs/qiskit_machine_learning.neural_networks.EstimatorQNN.html."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import RealAmplitudes, ZZFeatureMap


def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing a Quantum Neural Network (QNN) with a ZZ FeatureMap and a RealAmplitudes ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    feature_map = ZZFeatureMap(feature_dimension=num_qubits)
    ansatz = RealAmplitudes(num_qubits=num_qubits, reps=1)

    qc = QuantumCircuit(num_qubits)
    feature_map = feature_map.assign_parameters([1 for _ in range(feature_map.num_parameters)])

    rng = np.random.default_rng(10)
    ansatz = ansatz.assign_parameters(rng.random(ansatz.num_parameters) * 2 * np.pi)
    qc.compose(feature_map, inplace=True)
    qc.compose(ansatz, inplace=True)

    qc.name = "qnn"
    qc.measure_all()
    return qc
