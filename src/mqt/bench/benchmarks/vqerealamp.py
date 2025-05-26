# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""VQE realamp ansatz benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from qiskit.circuit import ParameterVector

try:
    from qiskit.circuit.library import real_amplitudes
except ImportError:
    from qiskit.circuit.library import RealAmplitudes as real_amplitudes  # noqa: N813


if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit


def create_circuit(num_qubits: int, reps: int = 3, random_parameters: bool = True) -> QuantumCircuit:
    """Returns a quantum circuit implementing the RealAmplitudes ansatz.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        reps: number of repetitions (layers) in the ansatz
        random_parameters: If True, assign random parameter values; if False, use symbolic parameters.

    Returns:
        QuantumCircuit: a quantum circuit implementing the RealAmplitudes ansatz
    """
    qc = real_amplitudes(num_qubits, entanglement="full", reps=reps)

    if random_parameters:
        rng = np.random.default_rng(10)
        num_params = qc.num_parameters
        qc = qc.assign_parameters(2 * np.pi * rng.random(num_params))
    else:
        param_vec = ParameterVector("p", length=qc.num_parameters)
        qc = qc.assign_parameters(param_vec)
    qc.name = "vqerealamp"

    qc.measure_all()
    return qc
