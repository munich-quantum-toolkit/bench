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
from qiskit.circuit.library import EfficientSU2

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing EfficientSU2 ansatz with random parameter values.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a quantum circuit implementing the EfficientSU2 ansatz with random parameter values
    """
    rng = np.random.default_rng(10)
    qc = EfficientSU2(num_qubits, entanglement="full", reps=3)
    num_params = qc.num_parameters
    qc = qc.assign_parameters(2 * np.pi * rng.random(num_params))
    qc.measure_all()
    qc.name = "vqesu2random"

    return qc
