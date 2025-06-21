# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Quantum Neural Network benchmark definition. Code is inspired by https://qiskit.org/ecosystem/machine-learning/stubs/qiskit_machine_learning.neural_networks.EstimatorQNN.html."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import real_amplitudes, z_feature_map

from ._registry import register_benchmark


@register_benchmark("qnn", description="Quantum Neural Network (QNN)")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing a Quantum Neural Network (QNN) with a ZZ FeatureMap and a RealAmplitudes ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    feature_map = z_feature_map(feature_dimension=num_qubits)
    ansatz = real_amplitudes(num_qubits=num_qubits, reps=1)

    qc = QuantumCircuit(num_qubits)

    qc.compose(feature_map, inplace=True)
    qc.compose(ansatz, inplace=True)

    qc.name = "qnn"
    qc.measure_all()
    return qc
