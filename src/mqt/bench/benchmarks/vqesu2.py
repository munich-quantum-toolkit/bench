# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE su2 ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

try:
    from qiskit.circuit.library import efficient_su2
except ImportError:
    from qiskit.circuit.library import EfficientSU2 as efficient_su2  # noqa: N813

from qiskit.circuit import ParameterVector

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


def create_circuit(num_qubits: int, reps: int = 3, random_parameters: bool = True) -> QuantumCircuit:
    """Returns a quantum circuit implementing the EfficientSU2 ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        reps: number of repetitions (layers) in the ansatz
        random_parameters: If True, assign random parameter values; if False, use symbolic parameters.

    Returns:
        QuantumCircuit: a quantum circuit implementing the EfficientSU2 ansatz
    """
    qc = efficient_su2(num_qubits, entanglement="full", reps=reps)

    if random_parameters:
        rng = np.random.default_rng(10)
        num_params = qc.num_parameters
        qc = qc.assign_parameters(2 * np.pi * rng.random(num_params))
    else:
        param_vec = ParameterVector("θ", length=qc.num_parameters)
        qc = qc.assign_parameters(param_vec)

    qc.measure_all()
    qc.name = "vqesu2"

    return qc
