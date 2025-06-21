# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Random benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.random import random_circuit

from ._registry import register_benchmark

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("randomcircuit", description="Random Quantum Circuit")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a random quantum circuit twice as deep as wide. The random gate span over four qubits maximum.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit

    Returns:
        QuantumCircuit: a random quantum circuit twice as deep as wide
    """
    qc = random_circuit(num_qubits, num_qubits * 2, measure=False, seed=10)
    qc.measure_all()
    qc.name = "randomcircuit"
    return qc
